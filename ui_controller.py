import re
import time
import ctypes
from dataclasses import dataclass
from textwrap import shorten
from rapidfuzz import fuzz
from pywinauto import Desktop
@dataclass(slots=True)
class Control:
    ui: object
    name: str
    kind: str
    auto_id: str
    rect: tuple
    identity: tuple
class UIController:
    """Fast Windows UIA controller. Public API: show_windows(), inspect(), resolve(), activate(), handle()."""
    TYPES={"Button","SplitButton","MenuItem","ListItem","TreeItem","TabItem","Hyperlink","CheckBox","RadioButton","ComboBox","DataItem"}
    ACTIONS={"Button":("invoke","click_input"),"SplitButton":("invoke","click_input"),"MenuItem":("invoke","click_input"),"Hyperlink":("invoke","click_input"),"CheckBox":("toggle","click_input"),"RadioButton":("select","click_input"),"ListItem":("click_input","select"),"DataItem":("click_input","select"),"TabItem":("select","click_input"),"TreeItem":("click_input","select","expand"),"ComboBox":("expand","click_input")}
    TYPE_SUFFIXES=((re.compile(r"\s+(?:button|btn)$",re.I),{"Button","SplitButton"}),(re.compile(r"\s+tab\s+item$",re.I),{"TabItem"}),(re.compile(r"\s+menu\s+item$",re.I),{"MenuItem"}),(re.compile(r"\s+list\s+item$",re.I),{"ListItem","DataItem"}),(re.compile(r"\s+tree\s+item$",re.I),{"TreeItem"}),(re.compile(r"\s+hyperlink$",re.I),{"Hyperlink"}),(re.compile(r"\s+checkbox$",re.I),{"CheckBox"}),(re.compile(r"\s+radio\s+button$",re.I),{"RadioButton"}),(re.compile(r"\s+combo\s+box$",re.I),{"ComboBox"}))
    INDEX_RE=re.compile(r"\s*#(\d+)\s*$")
    RESOURCE_RE=re.compile(r"\s*-\s*(?:memory|cpu|gpu|network|disk)\s*(?:usage|use)?\s*-\s*[\d.,]+\s*(?:%|[kmgt]?b(?:/s)?)\s*$",re.I)
    COMMAND_RE=re.compile(r"^(?:please\s+)?(?:(?:can|could|would)\s+you\s+)?(?:click|press|select|choose|tap|activate)\s+(?:the\s+)?",re.I)
    GW_OWNER=4
    def __init__(self,match_score=72,ambiguity_gap=8,cache_time=.6):
        self.desktop=Desktop(backend="uia")
        self.match_score=match_score
        self.ambiguity_gap=ambiguity_gap
        self.cache_time=cache_time
        self.control_cache={}
        self.window_cache={}
        self._get_window=ctypes.windll.user32.GetWindow
        self._get_window.argtypes=[ctypes.c_void_p,ctypes.c_uint]
        self._get_window.restype=ctypes.c_void_p
    @staticmethod
    def normalize(text):
        return " ".join(re.sub(r"[^\w\s-]"," ",(text or "").casefold()).split())
    @classmethod
    def clean_name(cls,text):
        text=(text or "").strip()
        return cls.RESOURCE_RE.sub("",text).strip(" -") or text
    @classmethod
    def split_index(cls,text):
        text=(text or "").strip()
        m=cls.INDEX_RE.search(text)
        return (text[:m.start()].strip(),int(m.group(1))) if m else (text,None)
    @classmethod
    def parse_query(cls,text):
        text,index=cls.split_index(text)
        raw=text.casefold()
        kinds=set()
        if re.search(r"\b(?:switch|go|navigate)\s+(?:to\s+)?",raw) and re.search(r"\btab\b",raw):
            kinds={"TabItem"}
            text=re.sub(r"^\s*(?:switch|go|navigate)\s+(?:to\s+)?(?:the\s+)?","",text,flags=re.I)
        elif re.search(r"\b(?:create|open|add)\s+(?:a\s+)?(?:new\s+)?tab\b",raw):
            kinds={"Button","SplitButton","MenuItem"}
            text=re.sub(r"^\s*(?:create|open|add)\s+(?:a\s+)?","",text,flags=re.I)
        else:
            text=cls.COMMAND_RE.sub("",text)
            for pattern,types in cls.TYPE_SUFFIXES:
                if pattern.search(text):
                    kinds=set(types);text=pattern.sub("",text);break
        return cls.normalize(text),index,kinds
    @staticmethod
    def short(text,width=55):
        return shorten((text or "(unnamed)").strip(),width=width,placeholder="...")
    @classmethod
    def score(cls,a,b):
        a,b=cls.normalize(a),cls.normalize(b)
        if not a or not b:return 0
        if a==b:return 100
        if a in b:return 98
        return max(fuzz.WRatio(a,b),fuzz.token_set_ratio(a,b))
    @staticmethod
    def rect(ui):
        try:
            r=ui.rectangle();return r.left,r.top,r.right,r.bottom
        except Exception:return 0,0,0,0
    def windows(self):
        out=[]
        for w in self.desktop.windows():
            try:
                title=w.window_text().strip()
                if title and w.is_visible():out.append((title,w))
            except Exception:pass
        return out
    def show_windows(self):
        print("\nVISIBLE WINDOWS")
        for i,(title,_) in enumerate(self.windows(),1):print(f"{i}. {self.short(title,65)}")
    def find_window(self,text):
        text,index=self.split_index(text);query=self.normalize(text)
        if not query:return None
        key=(query,index);cached=self.window_cache.get(key)
        if cached and time.monotonic()-cached[0]<self.cache_time:
            try:
                if cached[1].is_visible():return cached[1]
            except Exception:pass
        windows=self.windows()
        matches=[(t,w) for t,w in windows if self.normalize(t)==query] or [(t,w) for t,w in windows if query in self.normalize(t)]
        if not matches:
            ranked=sorted(((self.score(query,t),t,w) for t,w in windows),key=lambda x:x[0],reverse=True)
            matches=[(t,w) for score,t,w in ranked if score>=self.match_score]
        if not matches:return None
        matches.sort(key=lambda x:(self.rect(x[1])[1],self.rect(x[1])[0]))
        if index is not None:
            return matches[index-1][1] if 1<=index<=len(matches) else None
        if len(matches)>1:
            print("Multiple windows matched:")
            for i,(title,_) in enumerate(matches[:8],1):print(f"{i}. {self.short(title,65)}")
            print("Use #number, example: Chrome #2")
            return None
        self.window_cache[key]=(time.monotonic(),matches[0][1]);return matches[0][1]
    def _owned_by(self,hwnd,target):
        seen=set();owner=int(self._get_window(hwnd,self.GW_OWNER) or 0)
        while owner and owner not in seen:
            if owner==target:return True
            seen.add(owner);owner=int(self._get_window(owner,self.GW_OWNER) or 0)
        return False
    def _app_windows(self,target):
        out=[target]
        try:handle=target.handle
        except Exception:return out
        for w in self.desktop.windows():
            try:
                if w.handle!=handle and w.is_visible() and self._owned_by(w.handle,handle):out.append(w)
            except Exception:pass
        return out
    def _record(self,ui):
        try:
            info=ui.element_info;kind=info.control_type or ""
            if kind not in self.TYPES or not ui.is_visible():return None
            name=(info.name or "").strip()
            if not name:
                try:name=(ui.window_text() or "").strip()
                except Exception:name=""
            auto_id=(info.automation_id or "").strip()
            if not name and not auto_id:return None
            name=self.clean_name(name or auto_id);rect=self.rect(ui)
            try:runtime=tuple(info.runtime_id or ())
            except Exception:runtime=()
            identity=("runtime",runtime) if runtime else (info.process_id,kind,auto_id,rect)
            return Control(ui,name,kind,auto_id,rect,identity)
        except Exception:return None
    def _scan(self,window,kinds=None):
        if kinds:
            out=[]
            for kind in kinds:
                try:found=window.descendants(control_type=kind)
                except Exception:continue
                for ui in found:
                    item=self._record(ui)
                    if item:out.append(item)
            return out
        try:return [item for ui in window.descendants() if (item:=self._record(ui))]
        except Exception:return []
    def controls(self,window_name,kinds=None,fresh=False):
        target=self.find_window(window_name)
        if target is None:return []
        kinds=frozenset(kinds or ());key=(target.handle,kinds);cached=self.control_cache.get(key)
        if not fresh and cached and time.monotonic()-cached[0]<self.cache_time:return cached[1]
        data=[]
        for w in self._app_windows(target):data.extend(self._scan(w,kinds or None))
        data=list({x.identity:x for x in data}.values());data.sort(key=lambda x:(x.rect[1],x.rect[0],x.kind))
        self.control_cache[key]=(time.monotonic(),data);return data
    def context(self,item,depth=2):
        out=[]
        try:parent=item.ui.parent()
        except Exception:return ""
        for _ in range(depth):
            if parent is None:break
            try:
                name=self.clean_name((parent.element_info.name or parent.window_text() or "").strip())
                if name and self.normalize(name)!=self.normalize(item.name):out.append(name)
            except Exception:pass
            try:parent=parent.parent()
            except Exception:break
        return " > ".join(out)
    def inspect(self,window_name):
        data=self.controls(window_name,fresh=True)
        print("\nACTIONABLE CONTROLS")
        for i,x in enumerate(data,1):print(f"{i}. {self.short(x.name)} [{x.kind}]")
        return [{"name":x.name,"type":x.kind,"automation_id":x.auto_id,"rect":x.rect} for x in data]
    def _options(self,items):
        return [{"number":i,"name":x.name,"type":x.kind,"context":self.context(x)} for i,x in enumerate(items[:10],1)]
    def _choose(self,items,index=None,interactive=True):
        items.sort(key=lambda x:(x.rect[1],x.rect[0]))
        if not items:return None
        if index is not None:return items[index-1] if 1<=index<=len(items) else None
        if len(items)==1:return items[0]
        options=self._options(items)
        if not interactive:return {"status":"ambiguous","options":options}
        print("\nMultiple controls matched:")
        for x in options:print(f"{x['number']}. {self.short(x['name'])} [{x['type']}]"+(f" | {self.short(x['context'],35)}" if x['context'] else ""))
        while True:
            answer=input(f"Choose 1-{len(options)} or 0 to cancel: ").strip()
            if answer=="0":return None
            if answer.isdigit() and 1<=int(answer)<=len(options):return items[int(answer)-1]
            print("Invalid choice.")
    def resolve(self,window_name,text,interactive=True):
        query,index,kinds=self.parse_query(text)
        if not query:return None
        data=self.controls(window_name,kinds=kinds or None)
        if kinds:data=[x for x in data if x.kind in kinds]
        if not data:return None
        exact=[x for x in data if query in {self.normalize(x.name),self.normalize(x.auto_id)}]
        if exact:return self._choose(exact,index,interactive)
        partial=[x for x in data if query in self.normalize(x.name)]
        if partial:return self._choose(partial,index,interactive)
        ranked=[]
        for x in data:
            candidate=" ".join(filter(None,[x.name,x.auto_id,self.context(x)]));score=self.score(query,candidate)
            if score>=self.match_score:ranked.append((score,x))
        ranked.sort(key=lambda x:(-x[0],x[1].rect[1],x[1].rect[0]))
        if not ranked:return None
        top=ranked[0][0];close=[x for score,x in ranked if top-score<self.ambiguity_gap]
        return self._choose(close,index,interactive)
    @staticmethod
    def _run(ui,methods):
        for name in methods:
            method=getattr(ui,name,None)
            if callable(method):
                try:method();return True
                except Exception:pass
        return False
    def activate(self,window_name,control_name,interactive=True):
        item=self.resolve(window_name,control_name,interactive)
        if isinstance(item,dict):return {"success":False,**item}
        if item is None:return {"success":False,"status":"not_found"}
        try:
            if not item.ui.is_enabled():return {"success":False,"status":"disabled","control":item.name,"type":item.kind}
        except Exception:pass
        self._run(item.ui,("scroll_into_view",))
        success=self._run(item.ui,self.ACTIONS.get(item.kind,("click_input",)))
        if success:self.control_cache.clear()
        return {"success":success,"status":"activated" if success else "failed","control":item.name,"type":item.kind}
    def refresh(self):
        self.control_cache.clear();self.window_cache.clear();return True
    def handle(self,action,window_name=None,control_name=None,interactive=True):
        action=self.normalize(action)
        if action in {"windows","show windows","list windows"}:self.show_windows();return {"success":True,"status":"windows"}
        if action in {"inspect","scan","controls"}:return {"success":True,"status":"inspected","controls":self.inspect(window_name)}
        if action in {"activate","click","press","select"}:return self.activate(window_name,control_name,interactive)
        if action=="refresh":return {"success":self.refresh(),"status":"refreshed"}
        return {"success":False,"status":"unsupported","error":f"Unsupported action: {action}"}
def main():
    ui=UIController()
    while True:
        print("\n1 Show windows | 2 Inspect | 3 Activate | 4 Refresh | 5 Exit")
        choice=input("Select: ").strip()
        try:
            if choice=="1":ui.show_windows()
            elif choice=="2":ui.inspect(input("Window: "))
            elif choice=="3":print(ui.activate(input("Window: "),input("Control: "),True))
            elif choice=="4":ui.refresh();print("UI refreshed.")
            elif choice=="5":break
            else:print("Invalid option.")
        except Exception as error:print(f"ERROR: {type(error).__name__}: {error}")
if __name__=="__main__":main()
