from playwright.sync_api import sync_playwright
import msgpack

def main():
  with sync_playwright() as p:
    br = p.chromium.launch(headless=False)
    pg = br.new_page()

    def ws_log(dom,dirr,data):
        try:
            if type(data)==list and all([type(x)==int for x in data]):
                try:
                    u=msgpack.Unpacker(raw=False)
                    u.feed(bytes(data))
                    for d in u:
                        print("["+dirr.upper()+"]",dom,"->",d)
                except Exception as eee:
                    print("["+dirr.upper()+"]",dom,"-> [msgpack fail]",data,"|",eee)
            else:
                print("["+dirr.upper()+"]",dom,"->",data)
        except Exception as ee:
            print("["+dirr.upper()+"]",dom,"-> [error]",data,"|",ee)

    pg.expose_function("__ws_hook__",ws_log)

    pg.add_init_script("""
        scr=document.createElement('script');
        scr.src='https://unpkg.com/msgpack-lite/dist/msgpack.min.js';
        scr.async=false;
        document.documentElement.appendChild(scr);
    """)

    pg.add_init_script("""
        wsD={};
        const OldWS=WebSocket;
        WebSocket=new Proxy(OldWS,{
          construct(t,args){
            const w=new t(...args);
            const domm=new URL(w.url).origin;
            if(!wsD[domm]){wsD[domm]={sent:[],received:[]};}
            
            const oldS=w.send;
            w.send=function(d){
                let p=d;
                try{
                    if(d instanceof ArrayBuffer || d instanceof Uint8Array || d instanceof DataView){
                        p=Array.from(new Uint8Array(d.buffer||d));
                    }
                }catch(e){p=d;}
                wsD[domm].sent.push(p);
                window.__ws_hook__(domm,"sent",p);
                return oldS.apply(this,arguments);
            };

            w.addEventListener("message",e=>{
                let p=e.data;
                try{
                    if(e.data instanceof ArrayBuffer || e.data instanceof Uint8Array || e.data instanceof DataView){
                        p=Array.from(new Uint8Array(e.data.buffer||e.data));
                    }
                }catch(ex){p=e.data;}
                wsD[domm].received.push(p);
                window.__ws_hook__(domm,"received",p);
            });

            return w;
          }
        });
    """)

    try:
        pg.goto("https://krunker.io/social.html")
        pg.wait_for_timeout(999999999)
    except Exception as eeee:
        print("goto error?", eeee)
    finally:
        br.close()

if __name__=="__main__":
    main()
