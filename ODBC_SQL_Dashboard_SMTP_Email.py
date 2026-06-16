import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import time
import numpy as np
import pandas as pd
import pyodbc
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.ticker import StrMethodFormatter
import warnings
warnings.filterwarnings('ignore')
myFmt = DateFormatter("%m-%d-%Y")

# Below we have a sample query to a server storing weather data. The idea is that we are retreiving data from a server
# and would like to generate charts to be put in an email
weather_sql_query = """
    SELECT DATE_ID, County, Temperature, Precipitation
    FROM db.Weather_Daily
    WHERE DATE_ID>=getdate()-31
    AND County like 'Distrito%'
    GROUP BY DATE_ID;
    """

# pyodbc will take existing ODBC DSN to run the SQL query. The output will be a pandas DataFrame.
cnxn = pyodbc.connect("DSN=Weather_Server")
weather_sql_query_res = pd.read_sql_query(weather_sql_query, cnxn)
cnxn.close()

# With the data store in a DtaFrame we can generate the KPI chart. In this case we are generating a linechart.
# Some countries may ask to change date format, and this example covers it.
x = pd.to_datetime(weather_sql_query_res['DATE_ID'], format="%Y/%m/%d", utc=False).dt.date
# Having everyday in the x label may result in unreadable labels. It is better to have only one or few dates.
# In this case we are choosing to show only sundays dates.
xlabel = x[pd.to_datetime(weather_sql_query_res['DATE_ID'], format="%Y/%m/%d", utc=False).dt.weekday == 6]
fig, ax = plt.subplots(figsize=(12.8, 4.8))
sns.set_theme(style="whitegrid")
plt.plot(x, weather_sql_query_res['Temperature'], linewidth=3)
plt.title('Distrito Nacional - Temperature - Daily Average')
plt.xlabel('Date')
plt.autoscale(enable=True, axis='x', tight=True)
plt.xticks(xlabel, rotation=90, ha='right')
plt.ylabel('Celcius')
plt.grid(b=True, which='major', color='grey', linestyle='dashed')
# Need to specify where to save the charts plot so we can take it later for email construcction.
plt.savefig('C:/dev/DN_Temperature.png', dpi=100, orientation='landscape', bbox_inches="tight")
plt.close()

strFrom = 'userInSMTPserver@domain.com'
strTo = 'userA@domain.com;userB@domain.com,userC@domain.com'

msgRoot = MIMEMultipart('related')
msgRoot['Subject'] = 'Weather Report - Automated Monitoring'
msgRoot['From'] =  strFrom
msgRoot['To'] = ", ".join(strTo)

# Encapsulate the plain and HTML versions of the message body in
# 'alternative' part, so message agents can decide which they want to display.
msgAlternative = MIMEMultipart('alternative')
msgRoot.attach(msgAlternative)

html = """
<body>
<p>Hello team.</p>
<p>Plase find below weather trend:</p>
<table style="background-color: #FFFFFF">
<tr>
    <td> <img src="cid:DN_Temperature" alt="DN_Temperature"> </td>
</tr>
</table>
</body>
"""

msgText = MIMEText(html, 'html')
msgAlternative.attach(msgText)

fp = open('C:/dev/DN_Temperature.png', 'rb')
msgImage = MIMEImage(fp.read())
fp.close()

msgImage.add_header('Content-ID', '<DN_Temperature>')
msgRoot.attach(msgImage)

smtpObj = smtplib.SMTP('192.168.1.5')
smtpObj.set_debuglevel(1)
smtpObj.sendmail(strFrom, strTo, msgRoot.as_string())
smtpObj.quit()
print('eMail Sent')