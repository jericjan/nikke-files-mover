from pathlib import Path
from subprocess import Popen, PIPE

with open("adb_location.txt", encoding="utf-8") as f:    
    adb_location = f.read().strip()

local_files_folder = Path.cwd() / "files"
local_files_folder.mkdir(exist_ok=True)


def list_files(output_file):
    with open(output_file, "w", encoding="utf-8") as myoutput:
        coms = [
            adb_location,
            "shell",
            "ls",
            "-R",
            "-1",
            "-p",
            "/sdcard/Android/data/com.proximabeta.nikke/files",
        ]
        with Popen(coms, stdout=myoutput, stderr=PIPE, encoding="utf-8") as process:
            process.communicate()


def get_new_files():
    list_files("new_ls.txt")


def get_old_files():
    list_files("old_ls.txt")


def differentiate(path1, path2):
    def add_full(path):
        return f"{Path(path).stem}_full.txt"

    def get_lines(path):
        with Path(path).open(encoding="utf-8") as f:
            lines = f.readlines()
        return lines

    for path in [path1, path2]:
        fixed_lines = ""
        parent_dir = ""
        with Path(path).open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.endswith(":"):
                    parent_dir = line[:-1]
                elif line.endswith("/"):
                    pass
                elif line != "":
                    fixed_lines += f"{parent_dir}/{line}\n"

        with Path(add_full(path)).open("w", encoding="utf-8") as f:
            f.write(fixed_lines)

    path1 = get_lines(add_full(path1))
    path2 = get_lines(add_full(path2))

    with Path("new_not_in_old.txt").open("w", encoding="utf-8") as f:
        f.write("".join([x for x in path1 if x not in path2]))

    with Path("old_not_in_new.txt").open("w", encoding="utf-8") as f:
        f.write("".join([x for x in path2 if x not in path1]))


def copy_new_files(adb_location):
    base_path = "/sdcard/Android/data/com.proximabeta.nikke/files/"
    with Path("old_not_in_new.txt").open(encoding="utf-8") as deletable:
        deletable = deletable.read()
        if deletable != "":
            with Path("new_not_in_old.txt").open(encoding="utf-8") as movable:
                item_count = len(movable.readlines())
                for idx, line in enumerate(movable):
                    to_folder = local_files_folder / line[len(base_path) :]
                    to_folder = to_folder.parent
                    to_folder.mkdir(parents=True, exist_ok=True)
                    coms = [adb_location, "pull", line.strip(), str(to_folder)]
                    with Popen(coms, stdout=PIPE, stderr=PIPE, encoding="utf-8") as process:
                        stdout, stderr = process.communicate()
                    print(f"({idx+1} \\ {item_count}) copying files one by one")
                    print(stdout)
        else:
            coms = [adb_location, "pull", f"{base_path}.", str(local_files_folder)]
            with Popen(coms, stdout=PIPE, stderr=PIPE) as process:
                while True:  # Could be more pythonic with := in Python3.8+
                    line = process.stdout.readline()
                    if not line and process.poll() is not None:
                        break
                    print("copying all files in new device's folder")
                    print(line.decode())        

def delete_unused_files(adb_location):
    with Path("old_not_in_new.txt").open(encoding="utf-8") as f:
        item_count = len(f.readlines())
        for idx, line in enumerate(f):
            coms = [adb_location, "shell", "rm", line.strip()]
            with Popen(coms, stdout=PIPE, stderr=PIPE, encoding="utf-8") as process:
                stdout, stderr = process.communicate()
            print(stdout)
            print(stderr)
            print(f"({idx+1} \\ {item_count}) Deleting unused files in old device. Please wait.")


def copy_to_new(adb_location):
    android_files_path = "/sdcard/Android/data/com.proximabeta.nikke/files"

    coms = [adb_location, "push", str(local_files_folder) + "\\.", android_files_path]
    with Popen(coms, stdout=PIPE, stderr=PIPE) as process:
        while True:  # Could be more pythonic with := in Python3.8+
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            print(line.decode())


def connect_msg(step_num, name):
    input(
        f"({step_num}) Please ONLY connect the device that has the {name} and press ENTER..."
    )

def do_continue(msg):
    while True:
        user_input = input(f"\n{msg}\nPress ENTER to continue or type \"n\" to skip.").lower()
        if user_input == "":
            return True
        elif user_input == "n":
            return False
        else:
            print("Try again.")
        

while True:
    do_delete_files = input("Do you want to delete the log files? (y/n)").lower()
    if do_delete_files == "y":
        log_files = [x for x in Path('.').glob("*.txt") if x.name != "adb_location.txt"]
        for x in log_files:
            x.unlink(missing_ok=True)
        break
    elif do_delete_files == "n":
        break
    else:
        print("Incorrect input. Try again")

if not Path("new_ls.txt").exists():
    connect_msg(1, "updated NIKKE files")
    yes_continue = do_continue("This step will get the list of files on the new device.")    
    if yes_continue:
        get_new_files()

if not Path("old_ls.txt").exists():
    connect_msg(2, "old files")
    yes_continue = do_continue("This step will get the list of files on the old device.")    
    if yes_continue:    
        get_old_files()

yes_continue = do_continue("This step will get the difference of the files between the two devices.")    
if yes_continue:   
    differentiate("new_ls.txt", "old_ls.txt")

with Path("old_not_in_new.txt").open(encoding="utf-8") as deletable:
    deletable = deletable.read()
with Path("new_not_in_old.txt").open(encoding="utf-8") as transferable:
    transferable = transferable.read()
    
if deletable == "" and transferable == "":
    print("Files match exactly. Exiting...")
    exit()

connect_msg(3, "updated NIKKE files")

yes_continue = do_continue("This step will copy the new files that exist on the new device to the PC.")    
if yes_continue:   
    copy_new_files(adb_location)

connect_msg(4, "old files")

yes_continue = do_continue("This step will delete unused files on the old device.")    
if yes_continue:   
    delete_unused_files(adb_location)
    
yes_continue = do_continue("This step will copy the new files from the PC to the old device.")    
if yes_continue:      
    copy_to_new(adb_location)

print("Done!")
