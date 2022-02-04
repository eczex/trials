from os import listdir, mkdir, path
from sqlite3 import paramstyle
from sys import argv, exit
from re import match
import face_recognition
from PIL import Image
from itertools import compress

HELP = """
Extract persons from photos.

Description:
    Extract faces from images. Compares faces. 
    Saves faces of each person to their own folder.

Usage:
    python face_recognition_try.py <source_path> [<destination_path> more]

Args:
    <source_path>       Required    Path to directory containing photos of people 
                                    (only absolute unix paths accepted).
    <destination_path>  Optional    Path to directory to save images of person's faces. 
                                    If ommited results will be saved in source_path.
    more                Optional    Compare each face with each other to find people that 
                                    look alike. May impact performance. If ommited program 
                                    won't compare faces that once been matched.

Examples:
    python face_recognition_try.py /photos
    python face_recognition_try.py /photos more
    python face_recognition_try.py /photos /result 
    python face_recognition_try.py /photos /result more
"""
NO_ARGS = 'You need to pass at least one argument.\n'
NO_DIR = 'No such directory: {}.\n'
BAD_ARGS = 'Unable to parse arguments.\n'

def parse_args(args):
    if not  args:
        exit(NO_ARGS + HELP)
    source = args[0]
    dest = source
    more = False
    if not path.isdir(source):
        exit(NO_DIR.format(source) + HELP)
    if len(args) > 1:
        if 'more' in args[1:]:
            more = True
        if args[1].startswith('/'):
            dest = args[1]
            if not path.isdir(dest):
                mkdir(dest)
        if not more and dest == source:
            exit(BAD_ARGS + HELP)
    return source, dest, more

def read_images(source):
    faces_data = []
    img_extensions = ('.png', '.jpeg', '.jpg')

    for img_name in listdir(source):
        if path.splitext(img_name)[1] in img_extensions:
            img_path = path.join(source, img_name)
            image = face_recognition.load_image_file(img_path)
            face_encodings = face_recognition.face_encodings(image)
            face_locations = face_recognition.face_locations(image)
            faces = []
            for face_location in face_locations:
                top, right, bottom, left = face_location
                face_image = image[top:bottom, left:right]
                pil_image = Image.fromarray(face_image)
                faces.append(pil_image)
            faces_data.extend(list(zip(face_encodings, faces)))
    return faces_data

def already_matched(groups, matched_faces):
    """
    If we already have a person having all this faces — that's the same person.
    If new set has more matched faces than previous — they could be different persons
    or we just found extra images for previous person.
    """
    for group in groups:
        if {face in group for face in matched_faces} == {True}:
            return True

def match_faces(faces_data, more):
    groups = []

    while len(faces_data) > 1:
        compare_with = faces_data[1:]
        compare_what = faces_data[0]
        mask_of_matched = face_recognition.compare_faces(
            [x[0] for x in compare_with], 
            compare_what[0]
        )
        matched_indexes = list(compress(range(len(compare_with)), mask_of_matched))
        matched_faces = [compare_with[i][1] for i in matched_indexes]
        matched_faces.append(compare_what[1])

        if more:
            if not already_matched(groups, matched_faces):
                groups.append(matched_faces)
            # Excluding only one face from future comparings.
            faces_data = compare_with
        else:
            groups.append(matched_faces)
            # Excluding all matched faces from future comparings.
            faces_data = [face for j, face in enumerate(compare_with) if j not in matched_indexes]
    
    if faces_data: 
        if not more or (more and not already_matched(groups, [faces_data[0][1], ])) :
            groups.append([faces_data[0][1], ])

    return groups

def find_last_person_folder_number(folder):
    """
    To separate results in case we run script twice with the same results directory.
    Directories like 'person003' to be recognized as 'person3'.
    """
    person_folders_nums = [
        int(f[len('person'):]) 
        for f in listdir(folder) 
        if match(r"^person\d*", f)
    ]
    return max(person_folders_nums) if person_folders_nums else 0

def save_faces(groups, dest):
    start_person = find_last_person_folder_number(dest) + 1

    for i, group in enumerate(groups):
        person_name = f'person{start_person + i}'
        path_to_person = path.join(dest, person_name)
        mkdir(path_to_person)
        for j, face in enumerate(group):
            img_name = f'face{j + 1}.jpg'
            path_to_save = path.join(dest, person_name, img_name)
            face.save(path_to_save)

def extract_faces(args):
    source, dest, more = parse_args(args)
    if not dest:
        dest = source
    faces_data = read_images(source)
    groups = match_faces(faces_data, more)
    save_faces(groups, dest)

if __name__ == '__main__':
    extract_faces(argv[1:])
