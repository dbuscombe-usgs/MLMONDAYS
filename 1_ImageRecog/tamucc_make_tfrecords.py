

###############################################################
## IMPORTS
###############################################################

from imports import *

#============================================

imdir = '/media/marda/TWOTB/USGS/DATA/tamucc_coastal_imagery/coastline_lr'
csvfile = '/media/marda/TWOTB/USGS/DATA/tamucc_coastal_imagery/tamucc_full.csv'
recoded_dir = '/media/marda/TWOTB/USGS/DATA/tamucc_coastal_imagery/full_recoded'
# os.mkdir(recoded_dir)
tfrecord_dir = '1_ImageRecog/data/tamucc/full/'+str(TARGET_SIZE)
# os.mkdir(tfrecord_dir)

#============================================

dat = pd.read_csv(csvfile)

CLASSES = np.unique(dat['class'].values)
print(CLASSES)

CLASSES = [c.encode() for c in CLASSES]

# for f,c in zip(dat.file.values, dat['class'].values):
#   shutil.copy(imdir+os.sep+f, recoded_dir+os.sep+c+'_'+f)


im, lab = read_image_and_label(recoded_dir+os.sep+'exposed_riprap_structures_IMG_0296_SecABD_Sum12_Pt1.jpg')
print(lab)

im, lab = read_image_and_label(recoded_dir+os.sep+'scarps_steep_slopes_clay_IMG_5311_SABay_2013.jpg')
print(lab)


nb_images=len(tf.io.gfile.glob(recoded_dir+os.sep+'*.jpg'))

SHARDS = int(nb_images / ims_per_shard) + (1 if nb_images % ims_per_shard != 0 else 0)
print(SHARDS)

shared_size = int(np.ceil(1.0 * nb_images / SHARDS))
print(shared_size)

tamucc_dataset = get_dataset_for_tfrecords(recoded_dir, shared_size)

write_records(tamucc_dataset, tfrecord_dir)

#
# tamucc_dataset = tf.data.Dataset.list_files(recoded_dir+os.sep+'*.jpg', seed=10000) # This also shuffles the images
# tamucc_dataset = tamucc_dataset.map(read_image_and_label)
# tamucc_dataset = tamucc_dataset.map(resize_and_crop_image, num_parallel_calls=AUTO)
#
# tamucc_dataset = tamucc_dataset.map(recompress_image, num_parallel_calls=AUTO)
# tamucc_dataset = tamucc_dataset.batch(shared_size)


# train_ds = get_training_dataset()
for imgs,lbls in tamucc_dataset.take(1):
  #print(lbls)
  for count,im in enumerate(imgs):
     plt.subplot(2,2,count+1)
     plt.imshow(im)
     plt.title(CLASSES[lbls.numpy()[count]], fontsize=8)
     plt.axis('off')
plt.show()

#
# for shard, (image, label) in enumerate(tamucc_dataset):
#   shard_size = image.numpy().shape[0]
#   filename = tfrecord_dir+os.sep+"tamucc" + "{:02d}-{}.tfrec".format(shard, shard_size)
#
#   with tf.io.TFRecordWriter(filename) as out_file:
#     for i in range(shard_size):
#       example = to_tfrecord(image.numpy()[i],label.numpy()[i], CLASSES)
#       print(example)
#       #out_file.write(example.SerializeToString())
#     print("Wrote file {} containing {} records".format(filename, shard_size))