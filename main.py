
from selenium import webdriver
import time
import os
import csv
import requests
import re
import json
import base64
from datetime import datetime
from datetime import timezone

with open('config.json') as cf:
    config = json.load(cf)

headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
    'Referer': 'https://assistingh.theranest.com'
}

cookies = {}
cases = {
    '----': '59ef77d0f00c9b3d14fa6b52',
    'Nurse Assessment': '59f672d3f00c9b2e64d92275',
    'Physical Therapy Evaluation': '5a0da3424d30052e2804601d',
    'PT Soap note': '5a0dbf204d30052e28061f0f',
    'Additional': '5a1b5f094d2fff20c00866da',
    'MD Order': '5a2082154d30020494667313',
    'Physical therapy': '5a3aefbb4d2fff5360c4b238',
    'Therapy Progress Note': '5a5698fa4d2fff4018e5612f',
    'Speech Therapy Assessment': '5a5cee874d2fff4520b18dde',
    'Speech Therapy UPOC': '5a5d2f594d30024520faaf8d',
    'SLP Soap note': '5a60f7e04d300242e08cac6a',
    'Occupational Therapy': '5a7a2d0b4d3002124427e6b9',
    'OT Soap note': '5a7a32b04d300212442855ca',
    'Occupational Therapy': '5a7a33024d30021244285ce3',
    '_': '5b8f07c5ac67a714786b4dfa',
    '__': '5b8f07c500efb003f049da46',
    'Occupational Therapy Evaluation 1': '5babeb6cfe6fb407880cca61',
    '___': '5c09e4034a1dae08f80382d6',
    'MSW Assessment': '5cafe25173147b19a44a8e0f'
}


def get_auth(username, password):
    driver = webdriver.Chrome()
    driver.get("https://assistingh.theranest.com/home/signin?ReturnUrl=%2fclients")
    time.sleep(3)

    input_name = driver.find_element_by_css_selector('input[name="Email"]')
    input_name.send_keys(username)
    time.sleep(2)

    input_pass = driver.find_element_by_css_selector('input[name="Password"]')
    input_pass.send_keys(password)
    time.sleep(2)

    btn_login = driver.find_element_by_css_selector('input.login')
    btn_login.click()
    time.sleep(3)

    _cookies = driver.get_cookies()
    #cookies = _cookies[0]
    for _cookie in _cookies:
        c_name = str(_cookie['name'])
        c_value = str(_cookie['value'])

        cookies[c_name] = c_value


    driver.close()


def get_clients(page, search_key):

    clients = []
    link = 'https://assistingh.theranest.com/api/clients/getListing'
    response = requests.get(link,
                            headers=headers, cookies=cookies)

    try:
        if response.status_code == 200:
            result = response.json()
            _clients = result['Clients']

            for _client in _clients:
                clients.append(_client)

            return clients
        else:
            print(response.status_code)
            return []
    except Exception as e:
        print('Get Client Exception:', str(e))
        return []

    return clients


def get_files(client_id, target=''):

    url = 'https://assistingh.theranest.com/api/files/manage/{}?cmd=open'.format(
        client_id)

    if target == '':
        url = url + '&target=&init=1&tree=1'
    else:
        url = url + '&target={}'.format(target)

    response = requests.get(url, headers=headers, cookies=cookies)

    try:
        if response.status_code == 200:
            result = response.json()
            files = result['files']
            return files
        else:
            print(response.status_code)
            return []
    except Exception as e:
        print('Get File Exception:', str(e))
        return []


def download_file(client_id, client_file, client_folder):

    file_hash = client_file['hash']
    file_name = client_file['name']

    if not os.path.exists(client_folder):
        try:
            os.mkdir(client_folder)
        except Exception as e:
            print('Folder Create Exception:', str(e))

    if client_file['mime'] != 'directory':
        if not os.path.exists(client_folder + '/' + file_name):
            print('File:', file_name)
            output_folder = client_folder
            response = requests.get('https://assistingh.theranest.com/api/files/manage/{}?cmd=file&target={}&download=1'.format(client_id, file_hash),
                                    headers=headers, cookies=cookies)
            try:
                if response.status_code == 200:
                    with open(output_folder + '/' + file_name, 'wb') as wf:
                        wf.write(response.content)
                else:
                    print(response.status_code)
                    return None
            except Exception as e:
                print('File Download Exception:', str(e))
                return None

            time.sleep(0.5)
    else:
        print('Folder:', file_name)
        _files = get_files(client_id, file_hash)
        for _file in _files:
            if file_hash != _file['hash']:
                download_file(client_id, _file,
                              client_folder + '/' + file_name)


def get_progress_notes(client_id, client_folder):
    file_name = client_folder + '/Note_' + client_id + '.pdf'
    if not os.path.exists(file_name):
        print('Note:', client_id)
        time.sleep(3)
        response = requests.get('https://assistingh.theranest.com/api/clients/print-notes?clientId={}&from=&to='.format(client_id),
                                headers=headers, cookies=cookies)
        try:
            if response.status_code == 200:
                with open(file_name, 'wb') as wf:
                    wf.write(response.content)
            else:
                print(response.status_code)
        except Exception as e:
            print('Get Note Exception:', str(e))


def get_input_notes(client_folder, case_id, input_name, input_key):
    items = []
    response = requests.get('https://assistingh.theranest.com/api/custom-forms/{}/input-{}'.format(input_key, case_id),
                            headers=headers, cookies=cookies)
    try:
        if response.status_code == 200:
            result = response.json()
            items = result['Items']
        else:
            print(response.status_code)
            return None
    except Exception as e:
        print('Get Inputs Exception:', str(e))
        return None

    for item in items:
        input_number = item['InputNumber']

        file_name = client_folder + '/' + input_name + '_' + str(input_number) + '.pdf'
        if not os.path.exists(file_name):
            print('Input:', input_name, ' - ', input_number)
            response = requests.get('https://assistingh.theranest.com/print/custom-forms/{}/input?levelEntityId={}&inputNumber={}'.format(input_key, case_id, input_number),
                                    headers=headers, cookies=cookies)
            try:
                if response.status_code == 200:
                    with open(file_name, 'wb') as wf:
                        wf.write(response.content)
                else:
                    print(response.status_code)
                    continue
            except Exception as e:
                print('Get Input Exception:', str(e))
                continue
            
            time.sleep(0.5)


if __name__ == "__main__":
    get_auth(config['username'], config['password'])

    outputs = config['output']
    if not os.path.exists(outputs):
        os.makedirs(outputs)

    clients = []

    search_key = config['search']

    page = 55
    # while True:
    #     _clients = get_clients(page, search_key)
    #
    #     if len(_clients) == 0:
    #         break
    #
    #     for _client in _clients:
    #         clients.append(_client)
    #
    #     print(len(clients))
    #
    #     page += 1
    clients = get_clients(page, search_key)
    if len(clients) == 0:
        print('Unable to get client list')
        quit()

    for client in clients:
        print('Client:', client['FullName'])
        client_folder = outputs + '/' + client['FullName']

        if not os.path.exists(client_folder):
            try:
                os.mkdir(client_folder)
            except Exception as e:
                print('Client Folder Exception:', str(e))

        client_id = client['Id']
        client_files = get_files(client_id)
        if len(client_files) > 1:
            for client_file in client_files:
                if 'volumeId' not in client_file:
                    download_file(client_id, client_file, client_folder)

        get_progress_notes(client_id, client_folder)

        case_id = ''
        try:
            case_url = client['CaseNotesUrl']
            if case_url.find('progress-notes') != -1:
                case_group = client['CaseNotesUrl'].split('/cases/progress-notes/')
                case_group = case_group[1].split('/')
                case_id = case_group[0]
        except Exception as e:
            print(case_url)
            print('Case Exception:', str(e))
            continue

        if case_id != '':
            for input_name, input_key in cases.items():
                get_input_notes(client_folder, case_id, input_name, input_key)
