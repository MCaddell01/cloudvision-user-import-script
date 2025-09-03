# Script to get user information from a CloudVision endpoint and write it to a .csv file

import requests, json, argparse, csv

def get_user_data(base_url, token):
    # confirm api access to cloudvision endpoint
    cvp_service = '/cvpservice/cvpInfo/getCvpInfo.do'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.get(f"{base_url}{cvp_service}", headers=headers, verify=True, timeout=10)
    print(f"Get CVP info status code: {response.status_code}")
    if response.status_code == 200:
        if 'errorCode' in response.text:
            print(f"Get CVP info response text: {response.text}")
            return None
    else:
        return None
    
    # get current users from cloudvision
    cvp_service = '/cvpservice/user/getUsers.do'
    headers = {'Authorization': 'Bearer {}'.format(token),\
            'Accept': 'application/json',
            'Content-Type': 'application/json'}
    response = requests.get(f"{base_url}{cvp_service}?startIndex=0&endIndex=1000", headers=headers, verify=True, timeout=20)
    print(f"Get current users response status code: {response.status_code}")
    if response.status_code == 200:
        if 'errorCode' in response.text:
            print(f"Get current users response text: {response.text}")
            return None
    else:
        print(f"Get current users response text: {response.text}")
        return None

    # reformat the reponse to combine list of roles with list of users
    roles = response.json()['roles']
    users = response.json()['users']
    items_to_keep = ['userId', 'firstName', 'lastName', 'email', 'contactNumber', \
                    'userType', 'userStatus', 'profile']
    user_data = [{item: user_item for item, user_item in d.items() if item in items_to_keep} for d in users]
    for users in user_data:
        userId = users.get('userId')
        if userId in roles:
            users['roles'] = roles[userId]
    return user_data

def main():
    
    parser = argparse.ArgumentParser(
        prog  = "Get CloudVision User Accounts",
        description = "Get a list of all user accounts from a CloudVision endpoint and write them to a .csv file.",
        epilog = "Text at the bottom of the help index."
    )

    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    required.add_argument('-i', '--identity', required=True, type=argparse.FileType('r', encoding='utf-8'), dest='identity_file', help='A JSON file containing the CloudVision URL and service account token')
    optional.add_argument('-f', '--file', default='users', type=str, dest='save_file_name', help='Name of file to write csv data to')
    args = parser.parse_args()

    with args.identity_file as f:
        identity_dict = json.load(f)
        base_url = identity_dict['base_url']
        token = identity_dict['token']

    user_data = get_user_data(base_url=base_url, token=token)
    # write data to .csv
    if user_data != None:
        fieldnames = list(user_data[0].keys())
        save_file = f'{args.save_file_name}.csv'
        with open(save_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(user_data)
        print("Data written successfully!")
    else: print("Could not create user data file.")

if __name__=="__main__":
    main()