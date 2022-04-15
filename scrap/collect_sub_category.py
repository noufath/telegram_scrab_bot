import psycopg2
import requests
from db_config.db_connect import Db_Connect
from string import Template
import re
import applogger

class CollectSubCategory():

    def __init__(self, urlapi, db_connection):
        self.urlapi = urlapi
        self.db = db_connection
        self.cursor = self.db._cursor
        
        self.SaveToDatabase(self.Collect_Sub_Category())
    
    def Collect_Sub_Category(self):
        url = self.urlapi
        resp = requests.get(url).json()
        _source = resp["data"]

        list_rec = list()
        for dt in _source:
            sub_category = dt.get('sub')
        
            for rec in sub_category:
                sub = str(rec['sub_sub'])
                sub_formated = sub.replace("\'","\"")
                sub_formated = sub_formated.replace("None","\"None\"")

                list_rec += (self.TextSanitize(str(rec['display_name'])), \
                    self.TextSanitize(str(rec['name'])), \
                    rec['catid'], \
                    rec['parent_category'], \
                    str(rec['is_adult']), \
                    str(rec['block_buyer_platform']), \
                    rec['sort_weight'],
                    sub_formated),

        return list_rec

    def TextSanitize(self, str):
        """Sanitizes a string so that it can be properly compiled in TeX.
        Escapes the most common TeX special characters: ~^_#%${}
        Removes backslashes.
        """
        s = re.sub('\\\\', '', str)
        s = re.sub(r'([_^$%&#{}])', r'\\\1', str)
        s = re.sub(r'\'', r'\\~{}', str)
        return s

    def SaveToDatabase(self, data):
        logger = applogger.AppLoger('info_log')

        cursor = self.db._cursor

        '''
        Template_SQL = ("INSERT INTO sub_category(display_name,name,catid,parent_category,is_adult,block_buyer_platform, sort_weight, sub_sub) "
                            "VALUES $list_recs "
                            "ON CONFLICT (catid) "
                            "DO UPDATE SET display_name=EXCLUDED.display_name, "
                            "name=EXCLUDED.name, parent_category=EXCLUDED.parent_category, "
                            "is_adult=EXCLUDED.is_adult, block_buyer_platform=EXCLUDED.block_buyer_platform, "
                            "sort_weight=EXCLUDED.sort_weight, "
                            "sub_sub=EXCLUDED.sub_sub;"
           )
        
        for rec in data:
            strSQL = Template(Template_SQL).substitute(
               list_recs=rec
            )
            
            self.db.execute(strSQL)
            logger.info("Saving sub category : {}".format(rec))
        
        logger.info("Finished Collecting Sub Category data")
        '''

        
        # change to use execute_mogrify for more speed saving data
        if data != []:
            format_string = '(' + ','.join(['%s', ]*len(data[0])) + ')\n'
            args_string = ','.join(cursor.mogrify(format_string, x).decode('utf-8') for x in data)

            str_SQL = ("INSERT INTO sub_category (display_name,name,catid,parent_category,is_adult,block_buyer_platform, sort_weight, sub_sub) VALUES " + args_string + " ON CONFLICT (catid) " 
                        "DO UPDATE SET display_name=EXCLUDED.display_name, "
                        "name=EXCLUDED.name, parent_category=EXCLUDED.parent_category, "
                        "is_adult=EXCLUDED.is_adult, block_buyer_platform=EXCLUDED.block_buyer_platform, "
                        "sort_weight=EXCLUDED.sort_weight,"
                        "sub_sub=EXCLUDED.sub_sub;")

            try:
                self.db.execute(str_SQL)
            except (Exception, psycopg2.DatabaseError) as error:
                logger.info("Error: %s" % error)
                self.db._connection.rollback()
                cursor.close()
                return 1

        logger.info("Finished Collecting Sub Category data")       