from github import Github


def main():
    g = Github()
    repo = g.get_repo('olisolomons/rent_manager.py')
    for release in repo.get_releases():
        print(f'{release}, {release.published_at}')


if __name__ == '__main__':
    main()
