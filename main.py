import argparse
import datetime
import requests
from github import Auth, Github
from yaspin import yaspin

def percentile(p, l):
    idx = int((float(p)/100.0)*len(l))
    return l[idx][0]


def count_lines_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses (4xx and 5xx)
    content = response.text
    lines = content.splitlines()
    return len(lines)

@yaspin(text="Loading pull requests...")
def get_merged_pulls(repo, last_days):
    deadline = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=last_days)
    pulls = repo.get_pulls(state='closed')
    ret = []
    page = 0
    while True:
        for pull in pulls.get_page(page):
            if pull.is_merged():
                if pull.created_at < deadline:
                    return ret
                size = count_lines_from_url(pull.diff_url)
                ret.append((pull, size))
        page += 1
    return ret

def print_stats(pulls, min_size=None, max_size=None):
    print()
    if not min_size and not max_size:
        print(f"{len(pulls)} pull requests in the last {args.days} days for {args.repository}")
    elif not min_size:
        pulls = [(d,p,s) for (d,p,s) in pulls if s < max_size]
        print(f"{len(pulls)} pull requests in the last {args.days} days for {args.repository} and max diff size {max_size} lines")
    elif not max_size:
        pulls = [(d,p,s) for (d,p,s) in pulls if s >= min_size]
        print(f"{len(pulls)} pull requests in the last {args.days} days for {args.repository} and min diff size {min_size} lines")
    else:
        pulls = [(d,p,s) for (d,p,s) in pulls if s >= min_size and s < max_size]
        print(f"{len(pulls)} pull requests in the last {args.days} days for {args.repository} and diff size from {min_size} up to {max_size} lines")
        
    avg = sum([d.total_seconds() for (d,_,_) in pulls]) / len(pulls)
    print(" median:", pulls[int(len(pulls)/2)][0])
    print("    60%:", percentile(60, pulls))
    print("    70%:", percentile(70, pulls))
    print("    80%:", percentile(80, pulls))
    print("    90%:", percentile(90, pulls))
    print("average:", datetime.timedelta(seconds=avg))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='github-stats',
        description='Check how long it takes to get a pull request merged in')
    parser.add_argument('-t', '--token', default="token.txt", type=argparse.FileType('r'), help="path to a file containing your github token")
    parser.add_argument('-r', '--repository', default='NordSecurity/libtelio', help="repository to check")
    parser.add_argument('-d', '--days', default='NordSecurity/libtelio', type=int, help="maximum age of the merged pull request")
    args = parser.parse_args()
    auth = Auth.Token(args.token.read())

    g = Github(auth=auth)

    repo = g.get_repo(args.repository)
    pulls = get_merged_pulls(repo, args.days)
    pulls = [(p.merged_at-p.created_at, p, size) for (p,size) in pulls]
    pulls.sort()
    for (duration,pull,size) in pulls:
        print(f"Pull {pull.number} ({size} lines) merged in {duration}")

    avg = sum([d.total_seconds() for (d,_,_) in pulls]) / len(pulls)
    
    print_stats(pulls)
    print_stats(pulls, max_size=20)
    print_stats(pulls, min_size=20, max_size=50)
    print_stats(pulls, min_size=50, max_size=200)
    print_stats(pulls, min_size=200, max_size=500)
    print_stats(pulls, min_size=500)
