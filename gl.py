import gitlab
import os
import json

from pymemcache.client import base

from env import env


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
            json.dump(data, f)

def write_to_memcached(key, value):
    mc_client.set(key, value)

def write_many_to_memcached(key_value_dict):
    mc_client.set_many(key_value_dict)

def write_all_projects_to_json(file_name='projects', visibility=DEFAULT_VISIBILITY):
    projects = get_all_projects(visibility)
    projects_dict = {}
    for p in projects:
        projects_dict[p.path] = p.id
    write_to_json(projects_dict, file_name)

def write_all_groups_to_json(file_name='groups', visibility=DEFAULT_VISIBILITY):
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

# print(gl.projects.get('22780804'))
# write_all_groups_to_json()
write_all_projects_to_json()