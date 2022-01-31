from os import listdir, mkdir, path
import face_recognition
from PIL import Image
from itertools import compress

encoded_faces = []
located_faces = []
folder = '/face_recognition'
# folder = path.expanduser(folder)
img_extensions = ('png', 'jpeg', 'jpg')

for img_name in listdir(folder):
    if img_name.split('.')[-1] in img_extensions:
        img_path = path.join(folder, img_name)
        image = face_recognition.load_image_file(img_path)
        face_encodings = face_recognition.face_encodings(image)
        encoded_faces.extend(face_encodings)
        face_locations = face_recognition.face_locations(image)
        faces = []
        for face_location in face_locations:
            top, right, bottom, left = face_location
            face_image = image[top:bottom, left:right]
            pil_image = Image.fromarray(face_image)
            faces.append(pil_image)
        located_faces.extend(faces)

assert len(located_faces) == len(encoded_faces), '!!!ACHTUNG!!!\nCounts of located and encoded faces don\'t match.'

groups = []
matched_nums = set()
faces_count = len(encoded_faces)
max_i = faces_count - 1

for i in range(max_i):
    if i in matched_nums:
        continue
    compare_with = encoded_faces[i + 1:]
    compare_what = encoded_faces[i]
    mask = face_recognition.compare_faces(
        compare_with, 
        compare_what
    )
    matched = list(compress(range(i + 1, faces_count), mask))
    matched.append(i)
    matched_nums.update(matched)
    matched_faces = [located_faces[j] for j in matched]
    groups.append(matched_faces)

for i, group in enumerate(groups):
    person_name = f'person{i + 1:03d}'
    if person_name not in listdir(folder):
        path_to_person = path.join(folder, person_name)
        mkdir(path_to_person)
    for j, face in enumerate(group):
        img_name = f'face{j + 1:03d}.jpg'
        path_to_save = path.join(folder, person_name, img_name)
        face.save(path_to_save)