class ifka_design():
    def __init__(self):
        self.style_css= """
            QWidget#MAIN {
            background-color: rgb(84,109,143);
            padding: 0 0px;
            } 
            QWidget {
            background-color: white;
            } 
            QPushButton{
            background-color: qlineargradient(x1: 0, y1: 0,
                                              x2: 0, y2: 1,
                                              stop: 0 rgb(84,109,143),
                                              stop: 1 rgb(44,59,78) );  
            text-align: left;                                                                              
            color: white;
            border-style: solid;
            border-width: 0.3px;
            border-color: black;
            border-radius: 5px;
            font: Arial white 25px;
            padding: 0 8px;
            min-width: 10em;
            min-height: 3em;
            }
            QPushButton#small {
            background-color: qlineargradient(x1: 0, y1: 0,
                                              x2: 0, y2: 1,
                                              stop: 0 rgb(84,109,143),
                                              stop: 1 rgb(44,59,78) );  
            text-align: left;                                                                              
            color: white;
            border-style: solid;
            border-width: 0.3px;
            border-color: black;
            border-radius: 2px;
            font: Arial white 10px;
            padding: 0 8px;
            min-width: 2em;
            min-height: 1em;
            }
            QPushButton:pressed{
            background-color: qlineargradient(x1: 0, y1: 0,
                                              x2: 0, y2: 1,
                                              stop: 1 rgb(84,109,143),
                                              stop: 0 rgb(44,59,78) );
            }
            QFrame#tabFrame {   
            background-color: white;     
            border: 0px solid ;    
              
            }
            
            QFrame#subFrame {            
            border: 0.1px solid ;
            border-radius: 3px;
            border-color: rgb(230,230,230);
            border-bottom-left-radius: 3px;
            border-bottom-right-radius: 3px;     
            padding: 0px;
            spacing: 0px;     
            }
            QLabel#subFrameLabel {
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
            background-color: qlineargradient(x1: 0, y1: 0,                                                
                                              x2: 0, y2: 1,
                                              stop: 1 rgb(228,232,235),                                              
                                              stop: 0 rgb(244,245,247) );    
            padding: 5px 0px;       
            }
            
            QLabel#inputLabel {
            border-top-left-radius: 3px;
            border-bottom-left-radius: 3px;
            background-color: qlineargradient(x1: 0, y1: 0,                                                
                                              x2: 0, y2: 1,
                                              stop: 1 rgb(228,232,235),                                              
                                              stop: 0 rgb(244,245,247) );    
            min-width: 8em;                 
            }
            QLineEdit#inputEdit {
            border-top-right-radius: 3px;
            border-bottom-right-radius: 3px;
            border: 1px solid rgb(230,230,230);                  
            }
            
            QTreeView{
            background-color: white;            
            }          
            
            QTabBar#subTabBar::tab {
            background-color:  qlineargradient(x1: 0, y1: 0,                                                
                                              x2: 0, y2: 1,
                                              stop: 0 rgb(175,171,171),
                                              stop: 1 rgb(208,206,206) );
            border: 0.3px solid black;
            border-bottom: 0px ;         
            font-size: 12;
            border-top-left-radius: 3px;
            border-top-right-radius: 3px;
            border-bottom-left-radius: 0px;
            border-bottom-right-radius: 0px;
            min-width: 8em;
            min-height: 1.3em;
            } 
            QTabBar#subTabBar::tab:selected {
            background-color:  qlineargradient(x1: 0, y1: 0,                                                
                                              x2: 0, y2: 1,
                                              stop: 0 rgb(84,109,143),
                                              stop: 1 rgb(44,59,78) );           
            color: white;                                                      
            } 
            QTabWidget#subTab::pane { /* The tab widget frame */
            border-top: 3px solid rgb(44,59,78);            
            background-color: white; 
            border-bottom: 0px
            }
            QTabWidget QSplitter {                  
            background-color: white;             
            }
            
            QTabBar::tab {
            background-color:  qlineargradient(x1: 0, y1: 0,                                                
                                              x2: 0, y2: 1,
                                              stop: 0 rgb(175,171,171),
                                              stop: 1 rgb(208,206,206) );
            border: 0.3px solid black;
            border-top: 0px ;         
            font-size: 10;
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: 3px;
            border-bottom-right-radius: 3px;
            min-width: 8em;
            min-height: 1.3em;
            } 
            QTabBar::tab:selected {
            background-color:  qlineargradient(x1: 0, y1: 0,                                                
                                              x2: 0, y2: 1,
                                              stop: 1 rgb(84,109,143),
                                              stop: 0 rgb(44,59,78) );           
             color: white;                                                      
            } 
            
            QTabWidget::pane { /* The tab widget frame */
            border-top: 0px;
            border-bottom: 3px solid rgb(44,59,78);    
             
            }   
            QTabBar#mainTabBar {   background-color:  rgb(84,109,143);}
            QTabBar#mainTabBar::tab {
            background-color:  rgb(84,109,143);
            color: white;
            border: 3px rgb(84,109,143);                    
            font-size: 10;            
            min-width: 3em;
            min-height: 8em;
            border-top-left-radius: 10px;
            border-bottom-left-radius: 10px;   
            border-top-right-radius: 0px;
            border-bottom-right-radius: 0px;  
            } 
            QTabBar#mainTabBar::tab:selected {           
            border-right: 0px;                     
            background-color:  white;           
            color: black;                                                                
            }                  
            QTabWidget#mainTab::pane { /* The tab widget frame */           
            border-top: 0px;
            border-left: 0px ;              
            }     
            QTableView{
            background-color: white;            
            }
            QTableView::item {border: 1px solid rgb(230,230,230);}
            QScrollBar:vertical { border: 0px solid ; background: rgb(223,221,221); }
            QScrollBar:horizontal  { border: 0px solid ; background: rgb(223,221,221);  }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal
             {
                 background-color: rgb(175,171,171);    
                 min-height: 5px;
                 border-radius: 4px;
             }
             QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical { height: 0px;}
             QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal { width: 0px;}
                      
            """