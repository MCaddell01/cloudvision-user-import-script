# A simple Python script which can make RESTful API call to an Arista
# CloudVision endpoint to get user information and create new users

import requests, json, argparse, csv, ast

def post_user_data(base_url, token, new_users):
    # confirm api access to CloudVision endpoint
    cvp_service = '/cvpservice/cvpInfo/getCvpInfo.do'
    headers = {'Authorization': 'Bearer {}'.format(token)}
    response = requests.get(f"{base_url}{cvp_service}", headers=headers, verify=True, timeout=10)
    print(f"Get CVP info status code: {response.status_code}")
    if response.status_code == 200:
        if 'errorCode' in response.text:
            print(f"Get CVP info response text: {response.text}")
            return False
    else:
        print(f"Get CVP info reponse text {response.text}")
        return False

    # reformat new_users to a format cloudvision can accept
    new_roles = {}
    for user in new_users:
        new_roles[user['userId']] = user['roles']
        user.pop('roles')

    # get current users from new cloudvision
    cvp_service = '/cvpservice/user/getUsers.do'
    headers = {'Authorization': 'Bearer {}'.format(token),\
            'Accept': 'application/json',
            'Content-Type': 'application/json'}
    response = requests.get(f"{base_url}{cvp_service}?startIndex=0&endIndex=1000", headers=headers, verify=True, timeout=10)
    print(f"Get current users response status code: {response.status_code}")
    if response.status_code == 200:
        if 'errorCode' in response.text:
            print(f"Get current users response text: {response.text}")
            return False
    else:
        print(f"Get current users response text: {response.text}")
        return False
    existing_users = response.json()['users']

    # get current roles from new cloudvision
    cvp_service = '/cvpservice/role/getRoles.do'
    headers = {'Authorization': 'Bearer {}'.format(token),\
            'Accept': 'application/json'}
    response = requests.get(f"{base_url}{cvp_service}?startIndex=0&endIndex=1000", headers=headers, verify=True, timeout=10)
    print(f"Get current roles response status code: {response.status_code}")
    if response.status_code == 200:
        if 'errorCode' in response.text:
            print(f"Get current roles response text: {response.text}")
            return False
    else:
        print(f"Get current roles response text: {response.text}")
        return False
    existing_roles = response.json()['roles']

    # remove pre-existing users and non-SSO user types
    list_of_existing_users = [user['userId'] for user in existing_users]
    filtered_users = []
    filtered_roles = {}
    for user in new_users:
        if user.get('userId') in list_of_existing_users:
            print(f'Removed {user.get('userId')} from the import list as it already exists on {base_url}')
        elif user.get('userType') != 'SSO':
            print(f'Removed {user.get('userId')} from the import list as it does not use SSO authentication')
        else:
            filtered_users.append(user)
            filtered_roles[user.get('userId')] = new_roles[user['userId']]

    # define list of new/filtered roles and existing roles and remove duplicates
    list_of_filtered_roles = []
    for role_list in filtered_roles.values():
        list_of_filtered_roles.extend(role_list)
    list_of_filtered_roles = list(dict.fromkeys(list_of_filtered_roles))
    list_of_existing_roles = []
    for role_list in existing_roles:
        list_of_existing_roles.append(role_list["name"])

    # check all roles exist
    for role in list_of_filtered_roles:
        if role not in list_of_existing_roles:
            print(f'Error: the \'{role}\' role does not exist on \'{base_url}\'')
            return False

    # check there are new users to create
    if len(filtered_users)==0:
        print("No new users to create")
        return False

    # post new users
    # users must be posted via individual api requests
    input(f"WARNING! You are about to create {len(filtered_users)} new user(s) on {base_url}, press enter to confirm: ")
    for user in filtered_users:
        role = filtered_roles.get(user['userId'])
        body = {'roles': role,
                'user': user}
        cvp_service = '/cvpservice/user/addUser.do'
        headers = {'accept': 'application/json',
                   'Content-Type': 'application/json',\
            'Authorization': 'Bearer {}'.format(token)}
        response = requests.post(f"{base_url}{cvp_service}", headers=headers, json=body,  verify=True, timeout=20)
        print(f"Post new users reponse status code: {response.status_code}")
        if response.status_code == 200:
            if 'errorCode' in response.text:
                print(f"Post new users reponse text: {response.text}")
                return False
            print(f"Created new user {user['userId']}")
        else:
            print(f"Post new users reponse text: {response.text}")
            return False

    # check new users now exist
    cvp_service = '/cvpservice/user/getUsers.do'
    headers = {'Authorization': 'Bearer {}'.format(token),\
            'Accept': 'application/json',
            'Content-Type': 'application/json'}
    response = requests.get(f"{base_url}{cvp_service}?startIndex=0&endIndex=1000", headers=headers, verify=True, timeout=10)
    print(f"Get new users response status code: {response.status_code}")
    if response.status_code == 200:
        if 'errorCode' in response.text:
            print(f"Get new users response text: {response.text}")
            return False
    else:
        print(f"Get new users response text: {response.text}")
        return None
    all_users = response.json()['users']
    users_to_create = [d['userId'] for d in filtered_users]
    newly_created_users = [d['userId'] for d in all_users]
    for user in users_to_create:
        if user not in newly_created_users:
            print(f"Error {user} has not been created")
            return False

    return True

def main():
    
    parser = argparse.ArgumentParser(
        prog  = "Post CloudVision User Accounts",
        description = "Post a list of users contained within a .csv file to a CloudVision endpoint",
        epilog = "Text at the bottom of the help index."
    )
    
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')

    # define arguments required to run the script
    required.add_argument('-i', '--identity', required=True, type=argparse.FileType('r', encoding='utf-8'), dest='identity_file', help='A JSON file containing the CloudVision URL and service account token')
    required.add_argument('-f', '--file', required=True, type=argparse.FileType('r', encoding='utf-8'), dest='user_file', help='CSV file to import user data from')
    args = parser.parse_args()

    with args.identity_file as f:
        identity_dict = json.load(f)
        base_url = identity_dict['base_url']
        token = identity_dict['token']
    new_users = []
    with args.user_file as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['roles'] = ast.literal_eval(row['roles'])
            new_users.append(dict(row))
    if (post_user_data(base_url=base_url, token=token, new_users=new_users)): print("All users created successfully!")
    else: print("Errors occured whilst trying to create new users.")
if __name__=="__main__":
    main()