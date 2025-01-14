# Written by Dr Daniel Buscombe, Marda Science LLC
# for "ML Mondays", a course supported by the USGS Community for Data Integration
# and the USGS Coastal Change Hazards Program
#
# MIT License
#
# Copyright (c) 2020, Marda Science LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

###############################################################
## IMPORTS
###############################################################
from imports import *

###############################################################
### DATA FUNCTIONS
###############################################################

#-----------------------------------
def get_training_dataset():
    """
    This function will return a batched dataset for model training
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: training_filenames
    OUTPUTS: batched data set object
    """
    return get_batched_dataset(training_filenames)

def get_validation_dataset():
    """
    This function will return a batched dataset for model validation
    INPUTS:
    OPTIONAL INPUTS:
    GLOBAL INPUTS:
    OUTPUTS:
    """
    return get_batched_dataset(validation_filenames)

# def get_validation_eval_dataset():
#     """
#     This function will return a test batched dataset for model testing
#     INPUTS:
#     OPTIONAL INPUTS:
#     GLOBAL INPUTS:
#     OUTPUTS:
#     """
#     return get_eval_dataset(validation_filenames)
# #
# #-----------------------------------
# def read_tfrecord(example):
#     """
#     This function
#     INPUTS:
#     OPTIONAL INPUTS:
#     GLOBAL INPUTS:
#     OUTPUTS:
#     """
#     features = {
#         "image": tf.io.FixedLenFeature([], tf.string),  # tf.string = bytestring (not text string)
#         "class": tf.io.FixedLenFeature([], tf.int64),   # shape [] means scalar
#     }
#     # decode the TFRecord
#     example = tf.io.parse_single_example(example, features)
#
#     image = tf.image.decode_jpeg(example['image'], channels=3)
#     image = tf.cast(image, tf.uint8) #float32) / 255.0
#     image = tf.reshape(image, [TARGET_SIZE,TARGET_SIZE, 3])
#
#     class_label = tf.cast(example['class'], tf.int32)
#
#     return image, class_label
#
# #-----------------------------------
# def get_batched_dataset(filenames):
#     """
#     This function
#     INPUTS:
#     OPTIONAL INPUTS:
#     GLOBAL INPUTS:
#     OUTPUTS: batched dataset object
#     """
#     option_no_order = tf.data.Options()
#     option_no_order.experimental_deterministic = True
#
#     dataset = tf.data.Dataset.list_files(filenames)
#     dataset = dataset.with_options(option_no_order)
#     dataset = dataset.interleave(tf.data.TFRecordDataset, cycle_length=16, num_parallel_calls=AUTO)
#     dataset = dataset.map(read_tfrecord, num_parallel_calls=AUTO)
#
#     dataset = dataset.cache() # This dataset fits in RAM
#     dataset = dataset.repeat()
#     dataset = dataset.shuffle(2048)
#     dataset = dataset.batch(BATCH_SIZE, drop_remainder=True) # drop_remainder will be needed on TPU
#     dataset = dataset.prefetch(AUTO) #
#
#     return dataset

###############################################################
### DATA FUNCTIONS
###############################################################

class AnchorPositivePairs(tf.keras.utils.Sequence):
    """
    This function
    INPUTS:
    OPTIONAL INPUTS:
    GLOBAL INPUTS:
    OUTPUTS:
    """
    def __init__(self, num_batchs):
        self.num_batchs = num_batchs

    def __len__(self):
        return self.num_batchs

    def __getitem__(self, _idx):
        x = np.empty((2, num_classes, TARGET_SIZE, TARGET_SIZE, 3), dtype=np.float32)
        for class_idx in range(num_classes):
            examples_for_class = class_idx_to_train_idxs[class_idx]
            anchor_idx = np.random.choice(examples_for_class)
            positive_idx = np.random.choice(examples_for_class)
            while positive_idx == anchor_idx:
                positive_idx = np.random.choice(examples_for_class)
            x[0, class_idx] = X_train[anchor_idx]
            x[1, class_idx] = X_train[positive_idx]
        return x

#
# def get_data_stuff(ds, num_batches):
#     """
#     "get_data_stuff" - This function extracts lists of images and corresponding labels for training or testing
#     INPUTS:
#         * ds [PrefetchDataset]: either get_training_dataset() or get_validation_dataset()
#         * num_batches [int]
#     OPTIONAL INPUTS: None
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * X [list]
#         * y [list]
#         * class_idx_to_train_idxs [collections.defaultdict]
#     """
#     X = []
#     y = []
#
#     for imgs,lbls in ds.take(num_batches):
#       y.append(lbls.numpy())
#       for im in imgs:
#         X.append(im)
#
#     X = np.array(X)
#     y = np.hstack(y)
#
#     # get X_train, y_train arrays
#     X = X.astype("float32")
#     y = np.squeeze(y)
#
#     class_idx_to_idxs = defaultdict(list)
#     for y_train_idx, y in enumerate(y):
#         class_idx_to_idxs[y].append(y)
#
#     return X, y, class_idx_to_idxs


###############################################################
## VARIABLES
###############################################################

## model inputs
data_path= os.getcwd().replace('4_UnsupImageRecog', '1_ImageRecog')+os.sep+"data/nwpu/full/224"
test_samples_fig = os.getcwd()+os.sep+'results/nwpu_sample_11class_model1_est24samples.png'

cm_filename = os.getcwd()+os.sep+'results/nwpu_sample_11class_model1_cm_val.png'

sample_data_path= os.getcwd().replace('4_UnsupImageRecog', '1_ImageRecog')+os.sep+"data/nwpu/full/sample"

filepath = os.getcwd()+os.sep+'results/nwpu_subset_11class_custom_best_weights_model1.h5'

hist_fig = os.getcwd()+os.sep+'results/nwpu_sample_11class_custom_model1.png'

# nn_fig = os.getcwd()+os.sep+'results/nwpu_sample_11class_custom_model1_acc_vs_nn.png'

trainsamples_fig = os.getcwd()+os.sep+'results/nwpu_sample_11class_trainsamples.png'

valsamples_fig = os.getcwd()+os.sep+'results/nwpu_sample_11class_validationsamples.png'

cm_fig = os.getcwd()+os.sep+'results/nwpu_sample_11class_cm_test.png'

json_file =  os.getcwd().replace('4_UnsupImageRecog', '1_ImageRecog')+os.sep+'data/nwpu/nwpu_11classes.json'



CLASSES = read_classes_from_json(json_file)
print(CLASSES)


###############################################################
## EXECUTION
###############################################################
filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*.tfrec'))

nb_images = ims_per_shard * len(filenames)
print(nb_images)

split = int(len(filenames) * VALIDATION_SPLIT)

training_filenames = filenames[split:]
validation_filenames = filenames[:split]

validation_steps = int(nb_images // len(filenames) * len(validation_filenames)) // BATCH_SIZE
steps_per_epoch = int(nb_images // len(filenames) * len(training_filenames)) // BATCH_SIZE

print(steps_per_epoch)
print(validation_steps)

train_ds = get_training_dataset()
plt.figure(figsize=(16,16))
for imgs,lbls in train_ds.take(1):
  #print(lbls)
  imgs = imgs[:BATCH_SIZE]
  lbls = lbls[:BATCH_SIZE]
  for count,im in enumerate(imgs):
     plt.subplot(int(BATCH_SIZE/2),int(BATCH_SIZE/2),count+1)
     plt.imshow(im)
     plt.title(CLASSES[lbls.numpy()[count]], fontsize=8)
     plt.axis('off')
# plt.show()
plt.savefig(trainsamples_fig, dpi=200, bbox_inches='tight')
plt.close('all')


val_ds = get_validation_dataset()
plt.figure(figsize=(16,16))
for imgs,lbls in val_ds.take(1):
  #print(lbls)
  imgs = imgs[:BATCH_SIZE]
  lbls = lbls[:BATCH_SIZE]
  for count,im in enumerate(imgs):
     plt.subplot(int(BATCH_SIZE/2),int(BATCH_SIZE/2),count+1)
     plt.imshow(im)
     plt.title(CLASSES[lbls.numpy()[count]], fontsize=8)
     plt.axis('off')
# plt.show()
plt.savefig(valsamples_fig, dpi=200, bbox_inches='tight')
plt.close('all')


training_filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*.tfrec'))
nb_images = ims_per_shard * len(training_filenames)
print(nb_images)

num_batches = int(((1-VALIDATION_SPLIT) * nb_images) / BATCH_SIZE)
print(num_batches)

num_batches = 200

X_train, ytrain, class_idx_to_train_idxs = get_data_stuff(get_training_dataset(), num_batches)

# num_classes = len(CLASSES)

model = get_embedding_model(TARGET_SIZE, num_classes, num_embed_dim)

num_batches = int(np.ceil(len(X_train) / len(CLASSES)))
print(num_batches)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
     metrics=['accuracy'],
)

earlystop = EarlyStopping(monitor="loss",
                              mode="min", patience=patience)

# set checkpoint file
model_checkpoint = ModelCheckpoint(filepath, monitor='loss',
                                verbose=0, save_best_only=True, mode='min',
                                save_weights_only = True)

callbacks = [model_checkpoint, earlystop]

do_train = False #True

# no internal validation, so no validation dataset
# what is this dfoing and how does it work

# show embeddings, etc

if do_train:
    history = model.fit(AnchorPositivePairs(num_batchs=num_batches), epochs=max_epochs, callbacks=callbacks)

    plt.figure(figsize = (10,10))
    plt.subplot(221)
    plt.plot(history.history["loss"])
    plt.xlabel('Model training epoch number')
    plt.ylabel('Loss (soft cosine distance)')

    plt.subplot(222)
    plt.plot(history.history["accuracy"])
    plt.xlabel('Model training epoch number')
    plt.ylabel('Accuracy')
    # plt.show()
    plt.savefig(hist_fig, dpi=200, bbox_inches='tight')
    plt.close('all')

else:
    model.load_weights(filepath)


K.clear_session()


#### classify

#we'll use them all, but this number could be as low as 2
num_dim_use = num_embed_dim #i.e. 8

## make functions

knn = fit_knn_to_embeddings(model, X_train, ytrain, num_dim_use)

del X_train, ytrain

X_test, ytest, class_idx_to_test_idxs = get_data_stuff(get_validation_dataset(), num_batches)

touse = 1000

embeddings_test = model.predict(X_test[:touse])
embeddings_test = tf.nn.l2_normalize(embeddings_test, axis=-1)
del X_test

print('KNN score: %f' % knn.score(embeddings_test[:,:num_dim_use], ytest[:touse]))


## save knn model
## save ann model
# load both and apply


y_pred = knn.predict(embeddings_test[:,:num_dim_use])

# cm = confusion_matrix(ytest[:touse], y_pred, normalize='true'')

p_confmat(ytest[:touse], y_pred, cm_filename, CLASSES, thres = 0.1)


## apply to image files

sample_filenames = sorted(tf.io.gfile.glob(sample_data_path+os.sep+'*.jpg'))

for f in sample_filenames[:10]:
    image = file2tensor(f)
    image = tf.cast(image, np.float32)

    embeddings_sample = model.predict(tf.expand_dims(image, 0))

    #knn.predict_proba(embeddings_sample[:,:2])
    obs_class = f.split('/')[-1].split('_IMG')[0]
    est_class = CLASSES[knn.predict(embeddings_sample[:,:num_dim_use])[0]].decode()

    print('pred:%s, est:%s' % (obs_class, est_class ) )
