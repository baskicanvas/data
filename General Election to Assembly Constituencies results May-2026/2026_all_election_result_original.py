from bs4 import BeautifulSoup
import requests
import pandas as pd

#  get the urls and max counting rounts for a state
# def get_state_info(state_name, cons_vote_info):
def get_state_info(state_id):
    base_url='https://results.eci.gov.in/ResultAcGenMay2026/partywiseresult-'+state_id+'.htm'
    headers = {'User-agent': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"'}
    html_text = requests.get(base_url, headers=headers).text

    base_url_soup = BeautifulSoup(html_text, 'lxml')
    # get all constituencies of tha state
    constituencies = base_url_soup.find_all("option")

    state_info={}
    max_rounds=0

    for constituency_index, constituency in enumerate(constituencies):
        constituency_info={}
        if not(constituency.attrs.get("value") == ""):
            constituencies_name_id = constituency.attrs.get("value")
            dash_index = constituency.contents[0].rfind('-')
            constituency_name = constituency.contents[0][:dash_index].strip()
            constituency_number = constituency.contents[0][(dash_index+1):].strip()
            constituency_info['constituency_id']=constituency_number
            constituency_info['rounwise_url'] = 'https://results.eci.gov.in/ResultAcGenMay2026/Roundwise'+constituencies_name_id+'.htm?ac='+constituency_number
            constituency_info['constituencywise_url']='https://results.eci.gov.in/ResultAcGenMay2026/Constituencywise'+ constituencies_name_id +'.htm'
            html_text=requests.get(constituency_info['rounwise_url'], headers=headers).text
            rounwise_url_soup=BeautifulSoup(html_text,'lxml')
            tabs=rounwise_url_soup.find_all('div',class_='custom-table tabcontent')
            # print(len(tabs))
            constituency_info['counting_rounds']=len(tabs)
            # find maximum counting rounds in all constituency
            if(len(tabs)>max_rounds):
                max_rounds=len(tabs)
            state_info[constituency_name]=constituency_info
    return state_info, max_rounds

# write the state constituencies data to the csv file
def write_constituencies_data(state_name,state_info,max_rounds):
    print('get_state_constituencies_data')
    index=0
    for constituency_name in state_info:
        constituency_data=[]
        constituency_eligible_votes_data=[]
        constituency_additional_data=[]
        index=index+1
        constituency_info=state_info[constituency_name]
        constituency_number=constituency_info['constituency_id']
        headers = {'User-agent': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"'}   
        html_text=requests.get(constituency_info['rounwise_url'], headers=headers).text
        rounwise_url_soup=BeautifulSoup(html_text,'lxml')
        tabs=rounwise_url_soup.find_all('div',class_="custom-table tabcontent")
        # create list
        #for tab_index, tab in enumerate(tabs):
        for round_number in range(max_rounds):
            if(round_number<len(tabs)):
                tab=tabs[round_number]
                tab_rows = tab.tbody.find_all('tr')
                #print(len(tab_rows))
                for tab_row_index, tab_row in enumerate(tab_rows):
                    tab_row_data = tab_row.find_all('td')
                    if(round_number == 0):
                        # if not the last row (total)
                        if(len(tab_row_data[0].text) > 0):
                            candidate_name=tab_row_data[0].text
                            candidate_party=tab_row_data[1].text
                            candidate_round_votes=tab_row_data[4].text
                            constituency_tab_data=(state_name,constituency_name,constituency_number,candidate_name,candidate_party,candidate_round_votes)
                            constituency_data.append(constituency_tab_data)
                    else:
                        # if not the last row (total)
                        if(len(tab_row_data[0].text) > 0):
                            y = (tab_row_data[4].text,)
                            constituency_data[tab_row_index] += y
            # add empty data to add the coma in the csv file
            else:
                for tab_row_index, tab_row in enumerate(constituency_data):
                    constituency_data[tab_row_index] += ('',)
        # add additional data like postal votes and total votes
        html_text=requests.get(constituency_info['constituencywise_url'], headers=headers).text
        constituencywise_url_soup=BeautifulSoup(html_text,'lxml')
        postal_div=constituencywise_url_soup.find('div',class_='table-responsive')
        postal_div_tr=postal_div.tbody.find_all('tr')
        total_polled_votes=0
        for row_index,tr in enumerate(postal_div_tr):
            postal_div_tr_td=tr.find_all('td')
            if(len(postal_div_tr_td)>1 and ((postal_div_tr_td[0].text).isnumeric())):
                evm_total_votes=postal_div_tr_td[3].text
                postal_votes=postal_div_tr_td[4].text
                total_votes=postal_div_tr_td[5].text
                percentage_votes=postal_div_tr_td[6].text
                total_polled_votes=total_polled_votes+int(total_votes)
                constituency_votes=(evm_total_votes,postal_votes,total_votes,percentage_votes)
                constituency_additional_data.append(constituency_votes)
        for tab_row_index, tab_row in enumerate(constituency_data):
            constituency_data[tab_row_index] += constituency_additional_data[tab_row_index]
            constituency_data[tab_row_index] +=(str(total_polled_votes),)

        df = pd.DataFrame(constituency_data)
        df.to_csv(state_name+'_2026'+'.csv', mode = 'a', index = False, header = False)
        print('csv writing: '+str(index))

# write header row
def write_csv_header(state_name, max_rounds):
    rounds=()
    for x in range(max_rounds):
        rounds += ('r' + str(x + 1),)
        csv_header = ('state','constituency','constituency number','candidate','party')+rounds
        csv_header += ('evm votes','postal votes','candidate total votes','candidate vote %','total polled votes')

    f = open(state_name+'_2026'+'.csv', 'w')
    for index, text in enumerate(csv_header):
        if(index < len(csv_header)-1):
            f.write(text + ',')
        else:
            f.write(text + '\n')
    f.close()

def get_state():
    states_name_id=[
        {
            'name':'Assam',
            'id':'S03'
        },
        {
            'name':'Kerala',
            'id':'S11'
        },
        {
            'name':'Puducherry',
            'id':'U07'
        },
        {
            'name':'Tamil Nadu',
            'id':'S22'
        },
        {
            'name':'West Bengal',
            'id':'S25'
        }
    ]
    # find corresponding state id
    for index, state_name_id in enumerate(states_name_id):
        state_name = state_name_id['name']
        state_id = state_name_id['id']
        # print(state_name+':'+state_id)
        print(state_name_id)

    stare_code = input('Select the state code:')

    for index, state_name_id in enumerate(states_name_id):
        if(state_name_id['id'] == stare_code):
            state_name = state_name_id['name']
            state_id = state_name_id['id']
            break
    return state_name, state_id

if __name__=='__main__':
    state_name, state_id = get_state()
    state_info, max_rounds = get_state_info(state_id)
    write_csv_header(state_name, max_rounds)
    write_constituencies_data(state_name, state_info, max_rounds)
    print('done')
