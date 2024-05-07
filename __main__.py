import sys, os, re, urllib.request as ur
from __init__ import GitUserbase, UnknownPackages, isOnPYPI

from argparse import ArgumentParser, SUPPRESS
from appdirs import user_config_dir

__package__ = "GITPIP"
__version__ = 1.0
if len(sys.argv) < 2:
    sys.argv += ["--help"]
configDir = user_config_dir(__package__)
os.makedirs(configDir, exist_ok=True)
userFilename = os.path.join(configDir, "users.txt")
if not os.path.exists(userFilename):
    open(userFilename, "w").close()

def applyArgsTemplate(parser : ArgumentParser, users=False, packages=False):
    if packages is True:
        parser.add_argument("packages", metavar="PACKAGE", nargs="+", default=[])
    if users is True:
        parser.add_argument("-u", "--user", "--users", dest="users", metavar="USER", nargs="+", action="extend", default=[])

parser = ArgumentParser(prog="GITPIP")
parser.add_argument("-v", "--version", action="version", version=str(__version__))

modes = parser.add_subparsers(title="Modes", metavar="")
for name, *aliases in [["install"], ["update", "upgrade", "reinstall"], ["remove", "uninstall"]]:
    modes.add_parser(name, aliases=aliases, argument_default=SUPPRESS, help=f"{name.capitalize()} packages")
modes.add_parser("users", help=f"Add/remove github users")

applyArgsTemplate(modes.choices["install"], users=True, packages=True)
applyArgsTemplate(modes.choices["update"],  users=True, packages=True)
applyArgsTemplate(modes.choices["remove"],              packages=True)

modes.choices["users"].add_argument("--add", metavar="Add", nargs="*", default=[])
modes.choices["users"].add_argument("--remove", dest="rm", metavar="Remove", nargs="*", default=[])

args = parser.parse_args(sys.argv[1:])

exe = ["py", "-m", "pip"] if os.name == "nt" else ["pip"]
mode = sys.argv[1].lower()

match mode:
    case "update" | "upgrade" | "reinstall":
        com = ["install", "--force-reinstall", "--no-deps"]
        users = GitUserbase(open(userFilename, "r+").read().strip().split() + args.users)
        packs = [users.findOnGit(p) or p for p in args.packages]
        if (badPacks := list(filter(lambda p: not p.startswith("git") and not isOnPYPI(p), packs))):
            raise UnknownPackages(badPacks, users.users)
        os.system(" ".join(exe+com+packs))
    case "remove" | "uninstall":
        com = ["uninstall"]
        packs = args.packages
        os.system(" ".join(exe+com+packs))
    case "install":
        com = ["install"]
        users = GitUserbase(open(userFilename, "r").read().strip().split() + args.users)
        packs = [users.findOnGit(p) or p for p in args.packages]
        if (badPacks := list(filter(lambda p: not p.startswith("git") and not isOnPYPI(p), packs))):
            raise UnknownPackages(badPacks, gitUsers=users.users)
        os.system(" ".join(exe+com+packs))
    case "users":
        users = set(open(userFilename, "r").read().strip().split())
        users.difference_update(args.rm)
        users.update(args.add)
        open(userFilename, "w").write("\n".join(users))
        users = list(users)
        for i in range(0, len(users), 3):
            print(" ".join(map("{:<19}".format, users[i:i+3])))
    case _:
        print(f"Unknown mode {mode!r}")
