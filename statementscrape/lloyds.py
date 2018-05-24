import datetime
from getpass import getpass
import io
import pandas as pd
import re
from robobrowser import RoboBrowser


today = datetime.date.today()


def get_statement(start=today-datetime.timedelta(days=365), end=today):
    browser = _login()
    statement = _download_range(browser, start, end)
    return statement
    

def _login():
    
    username = input('User ID: ')
    password = getpass('Password: ')
    
    browser = RoboBrowser(parser='html.parser')

    browser.open('http://online.lloydsbank.co.uk/personal/logon.login.jsp')

    form = browser.get_form('frmLogin')
    form['frmLogin:strCustomerLogin_userID'] = username
    form['frmLogin:strCustomerLogin_pwd'] = password
    browser.submit_form(form)
    
    mem_info = getpass('Memorable information: ').lower()
    
    form_name = 'frmentermemorableinformation1'
    option_name = ':strEnterMemorableInformation_memInfo{}'
    form = browser.get_form(form_name)
    indices = re.findall('Character (\d+) :', form.parsed.text)
    indices = [int(x) for x in indices]

    for i, idx in enumerate(indices):
        form[form_name + option_name.format(i+1)] = '&nbsp;' + mem_info[idx-1]
    browser.submit_form(form)

    assert 'Lloyds Bank - Personal Account Overview' in browser.parsed.title

    accounts = {}
    for link in browser.get_links():
        if 'lnkAccName' in link.attrs.get('id', ''):
            accounts[link.text] = link
    
    print('Accounts:', list(accounts))
    
    account = input('Account: ')
    
    browser.follow_link(accounts[account])
    export_link = browser.get_link(title='Export')
    browser.follow_link(export_link)
    
    return browser


def _download_short_range(browser, start, end):
    form = browser.get_form('export-statement-form')
    form['exportDateRange'] = 'between'
    form['searchDateFrom'] = start.strftime('%d/%m/%Y')
    form['searchDateTo'] = end.strftime('%d/%m/%Y')
    form['export-format'] = 'Internet banking text/spreadsheet (.CSV)'
    browser.submit_form(form)
    text = browser.parsed.text
    browser.back()
    if text.startswith('Transaction Date'):
        return pd.read_csv(io.StringIO(text))



def _split_range(start, end):
    ONE_MONTH = datetime.timedelta(days=30)
    ONE_DAY = datetime.timedelta(days=1)
    while end - start > ONE_MONTH:
        yield (end - ONE_MONTH, end)
        end -= ONE_MONTH + ONE_DAY
    yield (start, end)


def _download_range(browser, start, end):
    chunks = [
        _download_short_range(browser, start, end)
        for (start, end) in _split_range(start, end)
        ]
    return pd.concat(chunks, ignore_index=True, verify_integrity=True)


if __name__ == '__main__':
    print(get_statement())
