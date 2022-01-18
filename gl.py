import gitlab
import os
import json

from pymemcache.client import base
import requests

from env import env


DEFAULT_GROUPS_JSON_FILE="groups"
DEFAULT_PROJECTS_JSON_FILE="projects"
DEFAULT_UNIQUE_USERS_IDS_FILE="unique_users_ids"
DEFAULT_USERS_IDS_FILE="unique_users_specific_attributes"

GITLAB_API_USERS_URL_BASE="https://gitlab.com/api/v4/users"
GITLAB_API_PROJECTS_URL_BASE="https://gitlab.com/api/v4/projects"
GITLAB_API_GROUPS_URL_BASE="https://gitlab.com/api/v4/groups"

ADDRESS = env['GITLAB_ADDRESS']
TOKEN = env['GITLAB_TOKEN']
DEFAULT_VISIBILITY = env['DEFAULT_VISIBILITY']
ENABLE_MEMCACHED = env['ENABLE_MEMCACHED']


if ENABLE_MEMCACHED == 'True':
    mc_client = base.Client(('localhost', 11211))


gl = gitlab.Gitlab(ADDRESS, private_token=TOKEN)
gl.auth()


def get_all_projects(visibility=DEFAULT_VISIBILITY):
    return gl.projects.list(all=True, visibility=visibility)

def get_all_groups(visibility=DEFAULT_VISIBILITY):
    return gl.groups.list(all=True, visibility=visibility)

def write_to_json(data, file_name):
    try:
        os.remove(f'{file_name}.json')
        print(f'Found old {file_name} file, removed it.')
        print(f'Data will be written to the new {file_name} file.')
    except:
        print(f"couldn't find {file_name} file, created new: {file_name}.json")

    with open(f'{file_name}.json', 'w') as f:
            json.dump(data, f, ensure_ascii=False)

def read_from_json(file):
    with open(f"{file}.json") as f:
        data = json.load(f)
        return data

def get_groups_ids_from_json(file_name=DEFAULT_GROUPS_JSON_FILE):
    data = read_from_json(file_name)
    ids_list=[]
    for k, v in data.items():
        ids_list.append(v)
    return ids_list


def get_projects_ids_from_json(file_name=DEFAULT_PROJECTS_JSON_FILE):
    data = read_from_json(file_name)
    ids_list=[]
    for k, v in data.items():
        ids_list.append(v)
    return ids_list

def write_to_memcached(key, value):
    mc_client.set(key, value)

def write_many_to_memcached(key_value_dict):
    mc_client.set_many(key_value_dict)

def write_all_projects_to_json(file_name=DEFAULT_PROJECTS_JSON_FILE, visibility=DEFAULT_VISIBILITY):
    projects = get_all_projects(visibility)
    projects_dict = {}
    for p in projects:
        projects_dict[p.path] = p.id
    write_to_json(projects_dict, file_name)

def write_all_groups_to_json(file_name=DEFAULT_GROUPS_JSON_FILE, visibility=DEFAULT_VISIBILITY):
    groups = get_all_groups(visibility)
    groups_dict = {}
    for g in groups:
        groups_dict[g.path] = g.id
    write_to_json(groups_dict, file_name)


# Memcached не поддерживает пробелы в названии ключа, поэтому
# пока не ясно, насколько целесообразно его использовать, т.к.
# придется производить лишние манипуляции, форматировать ввод и вывод.
# Можно использовать url (path), в нем пробелы гитлаб меняет на деши ('-')
def write_all_projects_to_memcached(visibility=DEFAULT_VISIBILITY):
    projects = get_all_projects(visibility)
    projects_dict = {}
    for p in projects:
        projects_dict[g.path] = g.id
    write_many_to_memcached(projects_dict)

def write_all_groups_to_memcached(visibility=DEFAULT_VISIBILITY):
    groups = get_all_groups(visibility)
    groups_dict = {}
    for g in groups:
        groups_dict[g.path] = g.id
    write_many_to_memcached(groups_dict)

def get_unique_user_ids_from_groups():
    ids_list = get_groups_ids_from_json()
    users_ids=[]
    for id in ids_list:
        # print()
        # print(id)
        response = requests.get(f"{GITLAB_API_GROUPS_URL_BASE}/{id}/members?private_token={TOKEN}")
        # print(response.json())
        response_json = response.json()
        n = len(response_json)
        if n > 0:
            for i in response_json:
                users_ids.append(i['id'])
    users_ids_set = set(users_ids)
    return users_ids_set

def get_unique_user_logins_from_projects():
    ids_list = get_projects_ids_from_json()
    users_ids=[]
    for id in ids_list:
        response = requests.get(f"{GITLAB_API_PROJECTS_URL_BASE}/{id}/members?private_token={TOKEN}")
        response_json = response.json()
        n = len(response_json)
        if n > 0:
            for i in response_json:
                users_ids.append(i['id'])
    users_ids_set = set(users_ids)
    return users_ids_set

def get_summary_set():
    set_groups = get_unique_user_ids_from_groups()
    set_projects = get_unique_user_logins_from_projects()
    set_summary = set_groups.union(set_projects)
    return set_summary

def write_unique_users_ids_to_json():
    data = get_summary_set()
    data = list(data)
    write_to_json(data, DEFAULT_UNIQUE_USERS_IDS_FILE)

def get_specific_attribute_for_all_unique_users(attribute="username"):
    data = read_from_json(DEFAULT_UNIQUE_USERS_IDS_FILE)
    attr_dict = {}
    for id in data:
        attrs_dict = {}
        response = requests.get(f"{GITLAB_API_USERS_URL_BASE}/{id}?private_token={TOKEN}")
        response_json = response.json()
        attrs_dict[attribute] = response_json[attribute]
        attr_dict[id] = attrs_dict
    return attr_dict

def get_specific_attributes_for_all_unique_users(*attributes, attrs_tuple=None):
    # if type(attributes[0]) == tuple:
    #     attributes = attributes[0]
    attributes = attrs_tuple if attrs_tuple else attributes
    data = read_from_json(DEFAULT_UNIQUE_USERS_IDS_FILE)
    attr_dict = {}
    for id in data:
        attrs_dict = {}
        response = requests.get(f"{GITLAB_API_USERS_URL_BASE}/{id}?private_token={TOKEN}")
        response_json = response.json()
        for attr in attributes:
            attrs_dict[attr] = response_json[attr]
        attr_dict[id] = attrs_dict
    return attr_dict

def write_specific_attributes_for_all_unique_users_to_json(*attributes):
    data = get_specific_attributes_for_all_unique_users(attrs_tuple=attributes)
    # print(data)
    write_to_json(data, DEFAULT_USERS_IDS_FILE)

# Дописать
# projects = iterable collection (list, tuple)
def delete_user_from_specified_projects(user_query, projects, dry=False):
    for p in projects:
        # project = gl.projects.get()
        members = p.members.list(query=user_query)

def delete_user_from_all_projects(user_query, dry=False):
    projects = get_all_projects()
    del_members_projects_count = 0
    del_projects_count = 0

    for p in projects:
        print(f'Project "{p.path_with_namespace}" (id={p.id}) :', end='')

        # Query members.
        members = p.members.list(query=user_query)

        # Delete members.
        if len(members) == 0:
            print(' no users to delete', end='')
        else:
            del_projects_count += 1
            for m in members:
                print(f' delete {m.username} (id={m.id})', end='')
                del_members_projects_count += 1
                if not dry:
                    m.delete()
                    pass
        print()

def main():
    # examples:

    # print(gl.projects.get('22780804'))
    # write_all_groups_to_json()
    # write_all_projects_to_json()
    # print(get_groups_ids_from_json())
    # print(len(get_unique_user_ids_from_groups()))
    # write_unique_users_ids_to_json()
    # print(get_specific_attribute_for_all_unique_users("name"))
    # print(get_specific_attributes_for_all_unique_users("username"))
    # write_specific_attributes_for_all_unique_users_to_json("name", "username")

    # write_all_groups_to_json()
    # write_all_projects_to_json()
    # write_unique_users_ids_to_json()
    write_specific_attributes_for_all_unique_users_to_json("name", "username")

if __name__ == "__main__":
    main()
