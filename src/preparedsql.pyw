#-*- coding: cp949 -*-
#-*- vim: et ts=8 sw=4 sts=4

import wx
import wx.stc as stc
import re
import os
import time
import pywintypes
import shlex
import StringIO
import codecs
#import keyword

from myADO import *
import xml.etree.ElementTree as ET

faces = { 'times': 'Times New Roman',
          'mono' : 'Courier New',
          'helv' : 'Fixedsys',
          #'helv' : 'Terminal',
          #'helv' : 'Courier New',
          #'helv' : 'Consolas',
          #'helv' : 'Courier New Bold',
          #'helv' : 'MS Mincho',
          #'helv' : 'Lucida Console',
          'other': 'Comic Sans MS',
          'size' : 10,
          'size2': 8,
         }

# Don't use MODIFY keyword
WRITE_SQL_KEYWORD = ['ALTER', 'INSERT', 'CREATE', 'INSERT', 'UPDATE', 'DROP', 'MOVE', 'RENAME']

default_config = u"""<?xml version="1.0" encoding="utf-8" ?>
<root>
<item name="TEST">
<dsn>
<![CDATA[
Provider=MSDAORA.11;Data Source=XXX;User ID=XXXX;Password=XXXX;PLSQLRSet=1
]]>
</dsn>
<sql>
<body>
<![CDATA[
SELECT *
  FROM tab
WHERE 
  (
  %(search_where)s
  )
]]>
</body>
<search_where>
<![CDATA[
    TNAME like '%%%(word)s%%'
]]>
</search_where>
</sql>
</item>
</root>

"""

def escape(str):
    str.replace("'", "''")
    return str

def unescape(str):
    str.replace("''", "'")
    return str

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        #wx.Frame.__init__(self, parent, title=title, size=(400, 600),
        #        style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE)
        wx.Frame.__init__(self, parent, title=title, size=(400, 300),
                style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE|wx.STAY_ON_TOP)

        # control
        self.search = wx.SearchCtrl(self, size=(200,-1), style=wx.TE_PROCESS_ENTER)
        #self.search.ShowSearchButton(True)
        self.search.ShowCancelButton(True)
        self.text = stc.StyledTextCtrl(self, -1)
        #self.text.StyleSetSpec(stc.STC_STYLE_DEFAULT, "face:%(helv)s,size:%(size)d" % faces)

        self.text.CmdKeyAssign(ord('B'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMIN)
        self.text.CmdKeyAssign(ord('N'), stc.STC_SCMOD_CTRL, stc.STC_CMD_ZOOMOUT)

        #self.text.SetLexer(stc.STC_LEX_PYTHON)
        self.text.SetLexer(stc.STC_LEX_CPP)
        #self.text.SetKeyWords(0, " ".join(keyword.kwlist))

        self.text.SetProperty("fold", "1")
        self.text.SetProperty("tab.timmy.whinge.level", "1")
        self.text.SetMargins(0,0)

        self.text.SetViewWhiteSpace(False)
        self.text.SetEdgeMode(stc.STC_EDGE_BACKGROUND)
        self.text.SetEdgeColumn(78)


        self.text.SetMarginType(2, stc.STC_MARGIN_SYMBOL)
        self.text.SetMarginMask(2, stc.STC_MASK_FOLDERS)
        self.text.SetMarginSensitive(2, True)
        self.text.SetMarginWidth(2, 12)


        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDEROPEN,    stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDER,        stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDERSUB,     stc.STC_MARK_VLINE,             "white", "#808080")
        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDERTAIL,    stc.STC_MARK_LCORNER,           "white", "#808080")
        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDEREND,     stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDEROPENMID, stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.text.MarkerDefine(stc.STC_MARKNUM_FOLDERMIDTAIL, stc.STC_MARK_TCORNER,           "white", "#808080")


        self.text.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % faces)
        self.text.StyleClearAll()  # Reset all to be like the default

        self.text.StyleSetSpec(stc.STC_STYLE_DEFAULT,     "face:%(helv)s,size:%(size)d" % faces)
        self.text.StyleSetSpec(stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(helv)s,size:%(size2)d" % faces)
        self.text.StyleSetSpec(stc.STC_STYLE_CONTROLCHAR, "face:%(other)s" % faces)
        self.text.StyleSetSpec(stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.text.StyleSetSpec(stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")
 
        #self.text.SetKeyWords(0, u'LOGIN_ID');
        #self.text.StyleSetSpec(stc.STC_P_WORD, "fore:#0000FF,size:%(size)d" % faces)
        # Number
        self.text.StyleSetSpec(stc.STC_C_NUMBER, "fore:#FF0000,size:%(size)d" % faces)
        # String
        self.text.StyleSetSpec(stc.STC_C_STRING, "fore:#7F007F,face:%(helv)s,size:%(size)d" % faces)
        # Comments
        self.text.StyleSetSpec(stc.STC_C_COMMENTLINE, "fore:#007F00,face:%(helv)s,size:%(size)d" % faces)

        self.text.AutoCompSetIgnoreCase(True)

        self.text.SetCaretForeground("BLUE")
        self.text.SetSelBackground(1,"#000080")
        self.text.SetSelForeground(1,"white")

        # layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.search, 0, wx.GROW)
        sizer.Add(self.text, 1, wx.GROW|wx.ALL)
        self.SetSizer(sizer)

        # Set event bindings
        self.text.Bind(stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.text.UsePopUp(False)
        self.text.Bind(wx.EVT_RIGHT_UP, self.OnPopupMenuStyledText)
        
        self.Bind(wx.EVT_TEXT_ENTER, self.OnDoSearch, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancel, self.search)
        self.Bind(wx.EVT_TEXT, self.OnKeyDown, self.search)
        self.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.OnSearch, self.search)

        try:
            self.LoadConfig()
        except:
            wx.MessageBox("[Error] Loading XML Config File(utf-8)")
            self.Close(True)

        self.Show(True)

    def OnCancel(self, evt):
        self.search.Clear()

    def OnKeyDown(self, evt):
        #wx.MessageBox(`dir(evt)`)
        pass

    def OnMarginClick(self, evt):
        #lineClicked = self.text.LineFromPosition(evt.GetPosition())
        #self.text.ToggleFold(lineClicked)
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            if evt.GetShift() and evt.GetControl():
                self.FoldAll()
            else:
                lineClicked = self.text.LineFromPosition(evt.GetPosition())

                if self.text.GetFoldLevel(lineClicked) & stc.STC_FOLDLEVELHEADERFLAG:
                    if evt.GetShift():
                        self.text.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 1)
                    elif evt.GetControl():
                        if self.text.GetFoldExpanded(lineClicked):
                            self.text.SetFoldExpanded(lineClicked, False)
                            self.Expand(lineClicked, False, True, 0)
                        else:
                            self.text.SetFoldExpanded(lineClicked, True)
                            self.Expand(lineClicked, True, True, 100)
                    else:
                        self.text.ToggleFold(lineClicked)
 
    def FoldAll(self):
        lineCount = self.text.GetLineCount()
        expanding = True

        # find out if we are folding or unfolding
        for lineNum in range(lineCount):
            if self.text.GetFoldLevel(lineNum) & stc.STC_FOLDLEVELHEADERFLAG:
                expanding = not self.text.GetFoldExpanded(lineNum)
                break

        lineNum = 0

        while lineNum < lineCount:
            level = self.text.GetFoldLevel(lineNum)
            if level & stc.STC_FOLDLEVELHEADERFLAG and \
               (level & stc.STC_FOLDLEVELNUMBERMASK) == stc.STC_FOLDLEVELBASE:

                if expanding:
                    self.text.SetFoldExpanded(lineNum, True)
                    lineNum = self.Expand(lineNum, True)
                    lineNum = lineNum - 1
                else:
                    lastChild = self.text.GetLastChild(lineNum, -1)
                    self.text.SetFoldExpanded(lineNum, False)

                    if lastChild > lineNum:
                        self.text.HideLines(lineNum+1, lastChild)

            lineNum = lineNum + 1

    def Expand(self, line, doExpand, force=False, visLevels=0, level=-1):
        lastChild = self.text.GetLastChild(line, level)
        line = line + 1

        while line <= lastChild:
            if force:
                if visLevels > 0:
                    self.text.ShowLines(line, line)
                else:
                    self.text.HideLines(line, line)
            else:
                if doExpand:
                    self.text.ShowLines(line, line)

            if level == -1:
                level = self.text.GetFoldLevel(line)

            if level & stc.STC_FOLDLEVELHEADERFLAG:
                if force:
                    if visLevels > 1:
                        self.text.SetFoldExpanded(line, True)
                    else:
                        self.text.SetFoldExpanded(line, False)

                    line = self.Expand(line, doExpand, force, visLevels-1)

                else:
                    if doExpand and self.GetFoldExpanded(line):
                        line = self.Expand(line, True, force, visLevels-1)
                    else:
                        line = self.Expand(line, False, force, visLevels-1)
            else:
                line = line + 1

        return line

    def OnPopupMenuStyledText(self, evt):
        self.menu_styledtext.Delete(self.menu_styledtext.GetMenuItems()[0].Id)
        new_id = wx.NewId()
        self.menu_styledtext.Insert(0, new_id, self.item_name)
        self.Bind(wx.EVT_MENU, self.OnMenuStyledText, id=new_id)
        self.mapMenu[new_id] = self.item_name
        self.text.PopupMenu(self.menu_styledtext)

    def OnMenuStyledText(self, evt):
        name = self.mapMenu[evt.GetId()]
        self.SetInfo(name)
        self.search.SetValue(self.text.GetSelectedText())
        self.search.Disable()
        self.search.Update()
        self.RunSQL()
        self.search.Enable()
        self.search.SetFocus()

    def OnSearch(self, evt):
        pass

    def OnDoSearch(self, evt):
        txt = self.search.GetValue()
        self.search.Disable()
        self.search.Update()
        self.RunSQL()
        self.search.Enable()
        self.search.SetFocus()
        """
        # SetLexer 
        txt_len = self.text.GetLength()
        for word in self.word_list:
            pos = self.text.FindText(0, txt_len-1, word)
            pos = self.text.FindText(pos + len(word), txt_len-1, word)
            #wx.MessageBox('%d' % len(word.encode('cp949')))
            self.text.StyleSetSpec(9, "fore:#0000FF,bold")
            self.text.StartStyling(pos, 0xff)
            self.text.SetStyling(len(word.encode('utf-8')), 9)
            #self.text.EnsureCaretVisible()
        """

    def LoadConfig(self):
        self.menu_search = None
        self.menu_styledtext = None
        self_file = os.sys.argv[0]
        self.config_file = "%s.xml" % os.path.splitext(self_file)[0]
        if not os.path.exists(self.config_file):
            fd = codecs.open(self.config_file, "wt", encoding='utf-8')
            fd.write(default_config)
            fd.close()
        tree = ET.parse(self.config_file)

        item_list = tree.findall("item")
        self.item_names = [item.attrib["name"] for item in item_list]
        if len(self.item_names) == 0:
            wx.MessageBox("err:%s" % self.config_file)
            return
        self.mapDSN = {}
        self.mapSQL_body = {}
        self.mapSQL_search_where = {}
        self.mapMenu = {}
        for name in self.item_names:
            self.mapDSN[name] = [item.findtext("dsn") for item in item_list if item.attrib["name"] == name][0]
            self.mapSQL_body[name] = [item.findtext("sql/body") for item in item_list if item.attrib["name"] == name][0]
            self.mapSQL_search_where[name] = [item.findtext("sql/search_where") for item in item_list if item.attrib["name"] == name][0]
        self.SetInfo(self.item_names[0])

        if self.menu_search == None:
            self.menu_search = wx.Menu()
            for name in self.item_names:
                name_list = name.split("/") # sub menu
                dir_list = name_list[:-1]
                subMenu = self.menu_search
                for dir_name in dir_list:
                    menu_id = subMenu.FindItem(dir_name)
                    if menu_id == -1:
                        menu_item = subMenu.AppendSubMenu(wx.Menu(), dir_name)
                    else:
                        menu_item = subMenu.FindItemById(menu_id) 
                    subMenu = menu_item.GetSubMenu()
                new_id = wx.NewId()
                subMenu.Append(new_id, name_list[-1])
                self.Bind(wx.EVT_MENU, self.OnMenuSearch, id=new_id)
                self.mapMenu[new_id] = name

            self.search.SetMenu(self.menu_search)

        if self.menu_styledtext == None:
            self.menu_styledtext = wx.Menu()
            self.menu_styledtext.AppendSeparator()
            self.menu_styledtext.AppendSeparator()

            for name in self.item_names:
                name_list = name.split("/") # sub menu
                dir_list = name_list[:-1]
                subMenu = self.menu_styledtext
                for dir_name in dir_list:
                    menu_id = subMenu.FindItem(dir_name)
                    if menu_id == -1:
                        menu_item = subMenu.AppendSubMenu(wx.Menu(), dir_name)
                    else:
                        menu_item = subMenu.FindItemById(menu_id) 
                    subMenu = menu_item.GetSubMenu()
                new_id = wx.NewId()
                subMenu.Append(new_id, name_list[-1])
                self.Bind(wx.EVT_MENU, self.OnMenuStyledText, id=new_id)
                self.mapMenu[new_id] = name

    def OnMenuSearch(self, evt):
        name = self.mapMenu[evt.GetId()]
        self.SetInfo(name)
        #wx.MessageBox(self.search.GetValue())
        #self.search.SetValue(self.text.GetSelectedText())
        self.search.Disable()
        self.search.Update()
        self.RunSQL()
        self.search.Enable()
        self.search.SetFocus()

    def SetInfo(self, name):
        self.item_name = name
        self.SetTitle(name)
        self.DSN = self.mapDSN[name]
        self.sql = self.mapSQL_body[name]
        self.sql_where = self.mapSQL_search_where[name]
        tok_list = list(shlex.shlex(StringIO.StringIO(self.sql)))
        if True in [t.upper() in WRITE_SQL_KEYWORD for t in tok_list]:
            wx.MessageBox(" Only SELECT statement!!!")
            self.Close(True)
        tok_list = list(shlex.shlex(StringIO.StringIO(self.sql_where)))
        if True in [t.upper() in WRITE_SQL_KEYWORD for t in tok_list]:
            wx.MessageBox(" Only SELECT statement!!!")
            self.Close(True)

    def RunSQL(self):
        ado = ADO(self.DSN)
        search_txt = self.search.GetValue()
        search_txt.strip()
        if len(search_txt) == 0:
            return
        self.word_list = re.split(' ', search_txt)
        if len(self.word_list) == 0:
            return

        search_where = ""
        result = None
        fields = None
        for i, word in enumerate(self.word_list):
            if i != 0:
                search_where += " OR "
                search_where += "("
                search_where += self.sql_where % vars()
                search_where += ")"
            else:
                search_where += self.sql_where % vars()

        sql = self.sql % vars()
        """
        tok_list = list(shlex.shlex(StringIO.StringIO(sql)))
        if True in [t in ['ALTER', 'INSERT', 'CREATE', 'INSERT', 'UPDATE', 'DROP'] for t in tok_list]:
            wx.MessageBox(" Only SELECT statement!!!")
            return
        """

        try:
            
            result = ado.Open(sql)
            fields = ado.fields
        except Exception, e:
            msg = """ %s file, tnsnames.ora !!!
 * DSN info 
%s
%s
            """ % (self.config_file, self.DSN, `e`)
            self.text.ClearAll()
            self.text.AddText(msg)
            wx.MessageBox(sql)
            return
        finally:
            del ado

        self.text.ClearAll()

        z_result = zip(*result)
        z_max_len = [max([len((u"%s" % v).encode("cp949")) if type(v) in (str, unicode) else len('%s' % `v`) for v in z]) for z in z_result]
        """
        z_max_len = []
        for z in z_result:
            v_list = []
            for v in z:
                if type(v) in (str, unicode):
                    v_len = len((u"%s" % v).encode("cp949"))
                else:
                    v_len = len('%s' % `v`)
                v_list.append(v_len)
            z_max_len.append(max(v_list))
        """


        # view header
        """
        z_max_len = [max(l, len(fields[i])) for i, l in enumerate(z_max_len)]
        field_list = []
        for i, f in enumerate(fields):
            field_list.append(f.rjust(z_max_len[i]-(len(f.encode('cp949')) - len(f))))
        head = u"  %s\r\n" % ', '.join(field_list)
        self.text.AppendText(head)
        self.text.AppendText("%s\r\n" % ("-" * len(head)))
        """

        list_len = [len(k.encode('cp949')) for k in fields]
        diff_len = [len(k.encode('cp949'))-len(k) for k in fields]
        key_max_len = max(list_len)
        for row in result:
            line_data = []
            result_txt = u""
            for i, v in enumerate(row):
                if type(v) in (str, unicode):
                    val = v
                else:
                    val = ('%s' % `v`).decode('cp949')
                line_data.append(val.rjust(z_max_len[i]-(len(val.encode('cp949')) - len(val))))
                result_txt += u"%s : %s\r\n" % (fields[i].rjust(key_max_len-diff_len[i]), v)
            strHead = u"{[%s]\r\n" % ', '.join(line_data)
            strEnd = u"}\r\n"
            self.text.AppendText(strHead)
            self.text.AppendText(result_txt)
            self.text.AppendText(strEnd)
        #for i in range(self.text.GetLineCount()):
        #    self.text.SetFoldExpanded(i, False)

class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "preparedSQL")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

if __name__ == '__main__':
    try:
        app = MyApp(True)
        app.MainLoop()
    except Exception, e:
        wx.MessageBox(`e`)

