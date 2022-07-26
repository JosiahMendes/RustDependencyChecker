from base64 import decode
from genericpath import exists
import sys
import subprocess
import argparse
#_______________________________________________________________________

# Dictionaries value: package, value: arrays of
# 	Dictionaries of value: version, value: arrays of toplevel/repo
#{
# libc: {
# 	"0.2.121": [parsec_tools/toplevel, parsec/toplevel],
# 	"0.2.122": [parsec/toplevel]
# 	},
# libd: {
# 	"0.2.121": [toplevel/repo],
# 	"0.2.122": [toplevel/repo]
# 	}
#}

#_____________________________________________
def packageDependencyAnalysis(out_list, projectList):
	for project in projectList:
		projectUnparsedTree = subprocess.run(['cargo', 'tree'], cwd=project, stdout=subprocess.PIPE).stdout.decode('utf-8').splitlines()
		projectName, projectVersion = projectUnparsedTree[0].split(' ')[0], projectUnparsedTree[0].split(' ')[1]
		for line in projectUnparsedTree[1:]:
			subline = line.split(' ')
			# print(subline)
			# top level
			if len(subline) == 3 or len(subline) == 4:
				if len(subline) == 3:
					package, version = subline[-2], subline[-1]
				if len(subline) == 4:
					package, version = subline[-3], subline[-2]
				# print("top_level", package, version)
				sub_dict = {package: {version: {f"{projectName}/{projectVersion}/top_level"}}}
				out_list.update(sub_dict)
				last_top_level = sub_dict

			else:
				# skip the line with '*' (already processed)
				if subline[-1][1] != "*":
					if subline[-1] == "(proc-macro)\n":
						package, version = subline[-3], subline[-2]
					elif subline[-1] == "[build-dependencies]" or subline[-1] == "[dev-dependencies]":
						pass
					else:
						package, version = subline[-2], subline[-1]
					# print("child", package, version)

					if package in out_list:
						if version in out_list[package]:
							# print(version, out_list[package])
							out_list[package][version].add(f"{projectName}/{projectVersion}/"+"".join(list(last_top_level.keys())))
						else:
							out_list[package].update({version: {f"{projectName}/{projectVersion}/"+"".join(list(last_top_level.keys()))}})
					else:
						child_dict = {package: {version: {f"{projectName}/{projectVersion}/"+"".join(list(last_top_level.keys()))}}}
						out_list.update(child_dict)
		# print("=="*20)
		# print(out_list)
	return out_list

def dependencyCheck(packageDict):
	for package, versions in sorted(packageDict.items()):
		if len(versions) > 1:
			print("Multiple versions of the same package: " + '\033[93m' + package + '\033[0m' +" are depended on across multiple projects")
			for version ,value in sorted(versions.items()):
				outputString = ("\t" + '\033[93m' + version + '\033[0m' + " is used by \033[94m" + ", ".join(value) + '\033[0m')
				print(outputString.replace("top_level", " directly"))




def main() -> int:
	"""Given a list of Rust project directories, parses their dependencies and warns if there are common dependencies with different versions"""

	CLI=argparse.ArgumentParser(description='Given a list of Rust project directories, parses their dependencies and warns if there are common dependencies with different versions')
	CLI.add_argument('-d', '--dir', nargs='+', type=str, help='List of directories to parse')
	args = CLI.parse_args()

	# Check if Cargo command exists and if not terminate
	rc = subprocess.call(['cargo', '--version'], stdout=subprocess.DEVNULL)
	if rc != 0:
		print('Cargo is not installed')
		exit(1)

	packageDict = {}

	# Run Cargo Tree Command + Parse Cargo Tree Output
	packageDependencyAnalysis(packageDict, args.dir)

	# Check Project Dependencies

	dependencyCheck(packageDict)

	return 0

if __name__ == '__main__':
	sys.exit(main())