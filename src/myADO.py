# -*- coding: cp949 -*-
# vim: et ts=8 sts=4 sw=4  
#
# ADO DB Connect Module
# Ex)
# 
#    DSN = "Provider=MSDAORA.11;Data Source=XX;User ID=XX;Password=XXXX;PLSQLRSet=1"
#    ado = ADO(DSN)
#    result = ado.Open(XXX);
#    print result
#    del ado

#import dbi, odbc
import win32com.client
import os
import sys

constants = win32com.client.constants


class ADO:
    conn = None
    rs = None
    ret = [] 
    DSN = None
    fields = None
    def __init__(self, DSN):
        self.DSN = DSN

    def Execute(self, sql):
        self.conn = win32com.client.Dispatch('ADODB.Connection')

        self.conn.Open(DSN)
        self.conn.Execute(sql)
        self.conn.Close()

    def Open(self, sql):
        self.ret = [] 
        self.conn = win32com.client.Dispatch('ADODB.Connection')
        self.conn.Open(self.DSN)
            
        self.rs = win32com.client.Dispatch('ADODB.Recordset')
        self.rs.Cursorlocation = 3
        #self.rs.CursorType = 0 #adOpenForwardOnly
        #self.rs.LockType = 1 #adLockReadOnly
        #self.rs.Open(sql, self.conn,0,1)
        self.rs.Open(sql, self.conn, CursorType = 0, LockType = 1)
        
        self.fields = [field.Name for field in self.rs.Fields]
        count = self.rs.RecordCount
        for row in range(self.rs.RecordCount):
            if self.rs.EOF:
                break
            else:
                #one_row = {}
                one_row = []
                for field in self.fields:
                    #one_row[field] =  self.rs.Fields.Item(field).Value
                    one_row.append(self.rs.Fields.Item(field).Value)
                self.ret.append(one_row)
                self.rs.MoveNext()
        self.rs.Close()
        del self.rs
        self.conn.Close()
        del self.conn
        return self.ret

    def __del__(self):
        pass
        #pdb.set_trace()

if __name__ == "__main__":
    DSN = "Provider=MSDAORA.11;Data Source=XXX;User ID=xxx;Password=xxx;PLSQLRSet=1"
    ado = ADO(DSN)
    sql = """create table test(name varchar2(32))"""

    result = ado.Open(sql);
    del ado

    os.system("pause")

