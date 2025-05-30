import argparse
import datetime
from github import Auth, Github
from yaspin import yaspin

def percentile(p, l):
    idx = int((float(p)/100.0)*len(l))
    return l[idx][0]

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
                ret.append(pull)
        page += 1
    return ret

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
    pulls = [(p.merged_at-p.created_at, p) for p in pulls]
    pulls.sort()
    for (duration,pull) in pulls:
        print(f"Pull {pull.number} merged in {duration}")

    avg = sum([d.total_seconds() for (d,_) in pulls]) / len(pulls)
    
    print()
    print(f"{len(pulls)} pull requests in the last {args.days} days for {args.repository}")
    print(" median:", pulls[int(len(pulls)/2)][0])
    print("    60%:", percentile(60, pulls))
    print("    70%:", percentile(70, pulls))
    print("    80%:", percentile(80, pulls))
    print("    90%:", percentile(90, pulls))
    print("average:", datetime.timedelta(seconds=avg))
