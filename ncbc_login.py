import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with requests.Session() as s:

    """
    :authority: memberleap.com
    :method: POST
    :path: /members/gateway.php
    :scheme: https
    accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
    accept-encoding: gzip, deflate, br
    accept-language: en-US,en;q=0.9
    cache-control: max-age=0
    content-length: 72
    content-type: application/x-www-form-urlencoded
    cookie: _ga=GA1.2.623916638.1595363401; _gid=GA1.2.1808863711.1595363401
    origin: http://ncbeer.org
    referer: http://ncbeer.org/
    sec-fetch-dest: document
    sec-fetch-mode: navigate
    sec-fetch-site: cross-site
    sec-fetch-user: ?1
    upgrade-insecure-requests: 1
    user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
    """

    s.verify = False
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'Cookie': 'testck=test; PHPSESSID=386d5b4c90febae8f3cfc1f39746898f; last_login_org_id=NCCB',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
       }
    

    login_url = 'https://www.memberleap.com/members/gateway.php'


    response = s.post(login_url, headers=headers, data={'Username': 'kevin.thorngren@gmail.com', 
                                                        'Password': 'R3alal3!ncbc',
                                                        'org_id': 'NCCB'
                                                        })

    print(response.status_code)
    #print(response.text)

    for cookie in s.cookies:
        print('cookie domain = ' + cookie.domain)
        print('cookie name = ' + cookie.name)
        print('cookie value = ' + cookie.value)
        print('*************************************')


    #headers['cookie'] = '; '.join([x.name + '=' + x.value for x in response.cookies])

    #print( headers['cookie'])

    """
    
    headers['sec-fetch-dest'] = 'document'
    headers['sec-fetch-mode'] = 'navigate'
    headers['sec-fetch-site'] = 'none'
    
    headers['accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    """


    result = s.get('https://www.memberleap.com/members/secure/evr/reports/attendees_csv.php?evid=19543125')
    #result = s.get('https://memberleap.com/members/secure/evr/mlist.php', cookies=s.cookies, headers=headers)

    #print('\nrequest')
    #print(s.cookies)
    #print(s.headers)

    print(result.text)