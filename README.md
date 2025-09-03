# cloudvision-user-import-script

This repository contains scripts which may export or import users from or to an Arista CloudVision Portal (CVP) platform.

# Export users

The script 'export_users.py' will export users from the specified CVP platform and write them to a CSV file.

Users are exported using the '/cvpservice/user/getUsers.do' pathname and both the user roles & user details are returned in the response.
This script will filter the 'users' dictionary to only the required parameters and will append the assigned user roles as an additional key entry as follows;

```json
{"users": [
    {
      "userId": "testUser",
      "firstName": "Test",
      "lastName": "User",
      "email": "test.user@example.co.uk",
      "contactNumber": "01234 567890",
      "userType": "SSO",
      "userStatus": "Enabled",
      "profile": "userProfile",
      "roles": "[role1, role2, role3]"
    }
  ]
}
```

The 'users' dictionary is then written to a the CSV file, to be imported by the import script, in the following format:
| userId    | firstName | lastName | email                        | contactNumber | userType | userStatus | profile        | roles                   |
|-----------|-----------|----------|------------------------------|---------------|----------|------------|----------------|-------------------------|
| testUser  | Test      | User     | test.user@example.co.uk      | 01234 567890  | SSO      | Enabled    | userProfile    | ['role1', role2, role3] |
| testUser1 | Test      | User1    | test.user1@example.co.uk     | 09876 543210  | SSO      | Enabled    | userProfile    |    ['role2', role3]     |

Users are written to a CSV file to allow an administrator to bulk create a number of users and import them to a CVP platform using the import script.
Roles must be spcified as a list with the surrounding square brackets, even if only one role is entered.

You can run the script as follows;
```bash
python ./export_users.py --identity identities/on-prem.json --file users.csv
```
The '--identities' is required, the '--file' arguments is optional and can be used to specify a file name.

# Import users

The script 'import_users.py' will import users from a CSV file to the specifed CVP platform.
Checks are in place to ensure the import will be successful before attempting.
Firstly the script will get a list of the current users & roles from the platform.
It will remove any existing users or users which do not use 'SSO' authenticationin from the list, it will also confirm all applied roles exist on the platform.

The CSV file is reformatted into a JSON structure, this JSON is then iterated over to post each user to the CVP endpoint individually using the 'cvpservice/user/addUser.do' pathname.

The script will then get an updated list of users from CVP and will confirm all users have been created.

You can run the script as follows;
```bash
python ./import_users.py --identity identities/cvaas.json --file users.csv
```
Both the '--identities' and '--file' arguments are required.

# Authentication

Both scripts make use of the CloudVision REST API Explorer to get and post data. APIs are authenticated using Service Account Tokens generated from the CloudVision Settings menu and are to be stored in JSON format along with the endpoint URL in the 'identities/' folder as follows;
```json
{
    "base_url": "https://<cvp-url>",
    "token": "<service-account-token>"
}
```
A new identity is required for each CVP platform.
