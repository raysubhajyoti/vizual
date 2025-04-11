from flask import Flask, request, render_template, render_template_string, redirect, url_for , send_file
from pypdf import PdfWriter 
import google.generativeai as genai
import pandas as pd
import math
import os
import matplotlib.pyplot as plt
import io
import seaborn as  sns
matplotlib.use('agg')
app = Flask(__name__)

genai.configure(api_key="AIzaSyDcnxupwsL7t70lAbcsEE8dJgO53d-olwU")
model = genai.GenerativeModel('gemini-1.5-flash-002')
filename="https://gist.githubusercontent.com/noamross/e5d3e859aa0c794be10b/raw/b999fb4425b54c63cab088c0ce2c0d6ce961a563/cars.csv"
df=''
colnames='' #str(list(df))
task_done = False
done=[]
countdone=0



def generatesuggestions(df, numbv, dv):
    prompt = f'''Analyse the data in {df} and suggest the top {numbv} visualizations that can help in understanding the data well. 
           End each suggestion with a %. The dependent variable is {dv}, and it should figure in most visualizations.
           No explanation is needed. Don't suggest too many single-variable visualizations, however include at 
           least one single variable visualization suggestion with {dv} 
            Have a mix of plot types.'''
    goals = model.generate_content(prompt)
    return goals.text



def vizualize():
    global task_done, countdone
    path = "c:/users/jim/flask/static/"
    countdone=0
    for i in range(numbv):
        prompt = f'''Translate this {result1[i]} into a Python matplotlib and seaborn command.  ensure that axis labels are aslo included, 
        and plot has a appropriate title. Assume data is in dataframe {df} and column names are given here: {list(df)}. Dont plot or show the chart. just save it.
        The code should save the chart as a pdf file with name img{i}.pdf in /static directory. Keep figsize=(6,4). Close the plot.
         '''
        t = model.generate_content(prompt)
        code = t.text.replace('`', '#')
        #print(code)
        if os.path.exists(path +"/" + "img"+str(i)+".pdf"):
            os.remove(path +"/" + "img"+str(i)+".pdf")
        try:
            exec(code) # {},{'df': df, 'plt': plt, 'ax': ax})
        #img = io.BytesIO()
        #plt.savefig(img, format='png')
        #img.seek(0)
        #return base64.b64encode(img.getvalue()).decode()
        except Exception as e:
            pass
        if os.path.exists(path +"/" + "img"+str(i)+".pdf"):
            done[i] = "Successfully created ...!!"
        else:
            done[i]=" Failed .. to generate !"
        countdone = i+1
        if i%3 == 0 :
            time.sleep(10)


    #time.sleep(10)
    task_done = True





@app.route("/snapshot", methods=["GET", "POST"])

def indexsnap():
    global task_done, colnames, df
    filename = request.files['file']
    
    #print(filename)
    try:
        df=pd.read_csv(filename)
    except:
        df=pd.read_excel(filename)
    colnames= str(list(df))
    fiverecords=df.head().to_html(classes='table table-striped', index=False)
    HTML_FORM = '''
    
    <!doctype html>
    <html>
    <head><title>User Input</title></head>
    <body>
     Here are the column names: ''' + colnames + ''' and sample data <li> ''' + df.head().to_html() + '''
    <form method="POST" action="/colnames">Which varibable in the dependent variable (you are most interested in) : 
        <input type="text" name="user_input" required>
        <input type="submit" value="Submit">
    </form>'''
    task_done = False 
    return render_template('sampledata.html',colnames=colnames, fiverecords=fiverecords)
    
@app.route("/colnames", methods=["GET", "POST"])
def index2():
    global result1, dv, numbv, done, df
    records=str(list(df))
    numbv= (len(list(df)) - 1 ) + 4
    for i in range(numbv):
        done.append("   ")
    if request.method == "POST":
        dv = request.form.get("user_input")
        result = generatesuggestions(df, numbv, dv)
        result = result.replace('%', '')
        result1 = result.split("\n")
    threading.Thread(target=vizualize).start()
    return redirect(url_for('waiting',  res=result, rec=str(records)))
    

@app.route("/waiting/<res>/<rec>")
def waiting(res,rec):
    global done
    timetomake = 14 * (numbv - countdone)
    k=res.split("\n")
    
    kkk=" "
    if task_done :
        done =[]
        return render_template('charts.html', label=k[0],numbv=numbv, summary=df.describe().to_html(classes='table table-striped', index=True))
       
    return render_template('viz.html', lines=enumerate(k),done=done, timetomake=timetomake)


@app.route("/",methods=["GET", "POST"])
def index():
    global done
    done =[]
    HTML_main = '''
<h2>Upload Excel File </h2>
<form method="POST" action ="/snapshot" enctype="multipart/form-data">
  <label>Upload Excel/CSV file:</label>
  <input type="file" name="file" accept=".xls,.xlsx, .csv" required><br><br>
  <!-- <label>Or paste URL to Excel file:</label>
  <input type="text" name="url"><br><br> -->
  <input type="submit" value="Submit">
</form>
'''
    return render_template_string(HTML_main)


@app.route("/download",methods=["GET", "POST"])  
def download_file():
    merger = PdfWriter()
    path = "static"
    imagepath =[]
    #dfi.export(df.describe().round(2), 'static/summary.png')
    #imagepath.append('static/summary.png')
    if os.path.exists("static/download.pdf"):
        os.remove("static/download.pdf")
    for i in range(numbv):
        if os.path.exists(path +"/" + "img"+str(i)+".pdf"):
            merger.append(path +"/" + "img"+str(i)+".pdf")
    #with open("static/download.pdf", "wb") as f:
        #f.write(img2pdf.convert(imagepath))
    merger.write("static/download.pdf")   
    for i in range(numbv):
        if os.path.exists(path +"/" + "img"+str(i)+".pdf"):        
            os.remove(path +"/" + "img"+str(i)+".pdf")
    return send_file("static/download.pdf", as_attachment=True)
    
app.run(debug=True)
