import json
import pandas as pd
from pyodide.ffi import to_js
from IPython.display import JSON, HTML
from js import Object, fetch
from io import StringIO

async def query(query_string, store = "L", set_na = False):
    
    # three Swiss triplestores
    if store == "F":
        address = 'https://fedlex.data.admin.ch/sparqlendpoint'
    elif store == "G":
        address = 'https://geo.ld.admin.ch/query'
    else:
        address = 'https://ld.admin.ch/query'
    
    # try the Post request with help of JS fetch
    # the creation of the request header is a little bit complicated because it needs to be a 
    # JavaScript JSON that is made within a Python source code
    try:
        resp = await fetch(address,
          method="POST",
          body="query=" + query_string.replace("+", "%2B").replace("&", "%26"),
          credentials="same-origin",
          headers=Object.fromEntries(to_js({"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", 
                                            "Accept": "text/csv" })),
        )
    except:
        raise RuntimeError("fetch failed")
    
    
    if resp.ok:
        res = await resp.text()
        # ld.admin.ch throws errors starting with '{"message":'
        if '{"message":' in res:
            error = json.loads(res)
            raise RuntimeError("SPARQL query malformed: " + error["message"])
        # geo.ld.admin.ch throws errors starting with 'Parse error:'
        elif 'Parse error:' in res:
            raise RuntimeError("SPARQL query malformed: " + res)
        else:
            # if everything works out, create a pandas dataframe from the csv result
            df = pd.read_csv(StringIO(res), dtype = str, na_filter = set_na)
            return df
    else:
        # fedlex.data.admin.ch throws error with response status 400
        if resp.status == 400:
            raise RuntimeError("Response status 400: Possible malformed SPARQL query. No syntactic advice available.")
        else:
            raise RuntimeError("Response status " + str(resp.status))
            
            
def display_result(df):
    df = HTML(df.to_html(render_links=True, escape=False))
    display(df)
