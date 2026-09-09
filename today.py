import datetime
from dateutil import relativedelta
import requests
import os
from lxml import etree
import hashlib

HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']
BIRTHDAY = datetime.datetime(2005, 7, 22)  # Your birthday


def daily_readme(birthday):
    """Returns the length of time since birthday"""
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years),
        diff.months, 'month' + format_plural(diff.months),
        diff.days, 'day' + format_plural(diff.days),
        ' :birthday:' if (diff.months == 0 and diff.days == 0) else '')


def format_plural(unit):
    return 's' if unit != 1 else ''


def simple_request(query, variables):
    """Makes a GraphQL request to GitHub API"""
    request = requests.post(
        'https://api.github.com/graphql',
        json={'query': query, 'variables': variables},
        headers=HEADERS
    )
    if request.status_code == 200:
        return request.json()
    raise Exception(f'Request failed: {request.status_code} {request.text}')


def get_user_stats():
    """Get repos, stars, and followers count"""
    query = '''
    query($login: String!) {
        user(login: $login) {
            repositories(ownerAffiliations: OWNER, first: 100) {
                totalCount
                nodes {
                    stargazerCount
                }
            }
            followers {
                totalCount
            }
        }
    }'''
    data = simple_request(query, {'login': USER_NAME})
    user = data['data']['user']
    repos = user['repositories']['totalCount']
    stars = sum(repo['stargazerCount'] for repo in user['repositories']['nodes'])
    followers = user['followers']['totalCount']
    return repos, stars, followers


def get_total_commits():
    """Get total commits across all years"""
    query = '''
    query($login: String!) {
        user(login: $login) {
            contributionsCollection {
                contributionCalendar {
                    totalContributions
                }
            }
        }
    }'''
    data = simple_request(query, {'login': USER_NAME})
    return data['data']['user']['contributionsCollection']['contributionCalendar']['totalContributions']


def svg_overwrite(filename, age_data, commit_data, star_data, repo_data, follower_data):
    """Parse SVG and update stats"""
    tree = etree.parse(filename)
    root = tree.getroot()

    update_element(root, 'age_data', age_data)
    update_element(root, 'commit_data', f'{commit_data:,}')
    update_element(root, 'star_data', str(star_data))
    update_element(root, 'repo_data', str(repo_data))
    update_element(root, 'follower_data', str(follower_data))

    tree.write(filename, encoding='utf-8', xml_declaration=True)


def update_element(root, element_id, new_text):
    """Find element by ID and update its text"""
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = str(new_text)


if __name__ == '__main__':
    print('Fetching GitHub stats...')

    # Calculate age/uptime
    age_data = daily_readme(BIRTHDAY)
    print(f'  Uptime: {age_data}')

    # Get GitHub stats
    repos, stars, followers = get_user_stats()
    print(f'  Repos: {repos}, Stars: {stars}, Followers: {followers}')

    commits = get_total_commits()
    print(f'  Commits: {commits}')

    # Update SVG files
    svg_overwrite('dark_mode.svg', age_data, commits, stars, repos, followers)
    svg_overwrite('light_mode.svg', age_data, commits, stars, repos, followers)

    print('SVG files updated!')
