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
#-----------------------------------
def get_training_dataset():
    """
    get_training_dataset()
    This function will return a batched dataset for model training
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: training_filenames
    OUTPUTS: batched data set object
    """
    return get_batched_dataset(training_filenames)

def get_validation_dataset():
    """
    get_validation_dataset()
    This function will return a batched dataset for model training
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: validation_filenames
    OUTPUTS: batched data set object
    """
    return get_batched_dataset(validation_filenames)

def get_validation_eval_dataset():
    """
    get_validation_eval_dataset()
    This function will return a batched dataset for model training
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: validation_filenames
    OUTPUTS: batched data set object
    """
    return get_eval_dataset(validation_filenames)

#-----------------------------------
def get_aug_datasets():
    """
    get_aug_datasets()
    This function will create train and validation sets based on a specific
    data augmentation pipeline consisting of random flipping, small rotations,
    translations and contrast adjustments
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: validation_filenames, training_filenames
    OUTPUTS: two batched data set objects, one for training and one for validation
    """
    data_augmentation = tf.keras.Sequential([
      tf.keras.layers.experimental.preprocessing.RandomFlip('horizontal'),
      tf.keras.layers.experimental.preprocessing.RandomRotation(0.01),
      tf.keras.layers.experimental.preprocessing.RandomTranslation(0.1,0.1),
      tf.keras.layers.experimental.preprocessing.RandomContrast(0.1)
    ])

    augmented_train_ds = get_training_dataset().map(
      lambda x, y: (data_augmentation(x, training=True), y))

    augmented_val_ds = get_validation_dataset().map(
      lambda x, y: (data_augmentation(x, training=True), y))
    return augmented_train_ds, augmented_val_ds

###############################################################
## VARIABLES
###############################################################

data_path= os.getcwd()+os.sep+"data/tamucc/subset_3class/400"

sample_data_path= os.getcwd()+os.sep+"data/tamucc/subset_3class/sample"

CLASSES = [b'marsh', b'dev', b'other']

#largeer patience
patience = 30

filepath = os.getcwd()+os.sep+'results/tamucc_subset_3class_mv2_best_weights_model3.h5'
weights_to_load = os.getcwd()+os.sep+'results/tamucc_subset_3class_mv2_best_weights_model2.h5'

train_hist_fig = os.getcwd()+os.sep+'results/tamucc_sample_3class_mv2_model3.png'
cm_filename = os.getcwd()+os.sep+'results/tamucc_sample_3class_mv2_model3_cm_val.png'
sample_plot_name = os.getcwd()+os.sep+'results/tamucc_sample_3class_mv2_model3_est24samples.png'

test_samples_fig = os.getcwd()+os.sep+'results/tamucc_full_sample_3class_mv2_model3_est24samples.png'

###############################################################
## EXECUTION
###############################################################

#images already shuffled

filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*.tfrec'))

print('.....................................')
print('Reading files and making datasets ...')

nb_images = ims_per_shard * len(filenames)
print(nb_images)

split = int(len(filenames) * VALIDATION_SPLIT)

training_filenames = filenames[split:]
validation_filenames = filenames[:split]

validation_steps = int(nb_images // len(filenames) * len(validation_filenames)) // BATCH_SIZE
steps_per_epoch = int(nb_images // len(filenames) * len(training_filenames)) // BATCH_SIZE

print(steps_per_epoch)
print(validation_steps)

## data augmentation is typically used
augmented_train_ds, augmented_val_ds = get_aug_datasets()

###########################################################
#### fine-tuning

print('.....................................')
print('Plotting learning rate scheduler ...')

### use smaller learning rate when fine tuning, and use more patience
lr_callback = tf.keras.callbacks.LearningRateScheduler(lambda epoch: lrfn(epoch), verbose=True)

rng = [i for i in range(MAX_EPOCHS)]
y = [lrfn(x) for x in rng]
plt.plot(rng, [lrfn(x) for x in rng])
# plt.show()
plt.savefig(os.getcwd()+os.sep+'results/learnratesched2.png', dpi=200, bbox_inches='tight')


### finet-tuned - load weights, then freeze lower layers

print('.....................................')
print('Creating and compiling model ...')

## use more dropout for regularization
dropout_rate =0.75
model3 = mobilenet_model(len(CLASSES), (TARGET_SIZE, TARGET_SIZE, 3), dropout_rate=dropout_rate)

model3.load_weights(weights_to_load)


print("Number of tunable layers in the base model: ", len(model3.layers))

# Fine-tune from this layer onwards
fine_tune_at = 80

# Freeze all the layers before the `fine_tune_at` layer
for layer in model3.layers[:fine_tune_at]:
  layer.trainable =  False

# check this: which layers are frozen?
for i,layer in enumerate(model3.layers):
    print('layer %i: %s' % (i, ['trainable' if layer.trainable else 'frozen'][0]))


model3.compile(optimizer=tf.keras.optimizers.Adam(), #1e-4),
          loss='sparse_categorical_crossentropy',
          metrics=['accuracy'])

earlystop = EarlyStopping(monitor="val_loss",
                              mode="min", patience=patience)

# set checkpoint file
model_checkpoint = ModelCheckpoint(filepath, monitor='val_loss',
                                verbose=0, save_best_only=True, mode='min',
                                save_weights_only = True)

callbacks = [model_checkpoint, earlystop, lr_callback]


do_train = False #True

if do_train:
    print('.....................................')
    print('Training model ...')

    # much slower to train
    history = model3.fit(augmented_train_ds, steps_per_epoch=steps_per_epoch, epochs=MAX_EPOCHS,
                          validation_data=augmented_val_ds, validation_steps=validation_steps,
                          callbacks=callbacks) #, class_weight = class_weights)

    # Plot training history
    plot_history(history, train_hist_fig)
    plt.close('all')
    K.clear_session()

else:
    model3.load_weights(filepath)


##########################################################
### evaluate
print('.....................................')
print('Evaluating model ...')

# loss, accuracy = model3.evaluate(get_validation_eval_dataset(), batch_size=BATCH_SIZE)
loss, accuracy = model3.evaluate(get_validation_dataset(), batch_size=BATCH_SIZE, steps=validation_steps)

print('Test Mean Accuracy: ', round((accuracy)*100, 2),' %')

##73

##########################################################
### predict
sample_filenames = sorted(tf.io.gfile.glob(sample_data_path+os.sep+'*.jpg'))

print('.....................................')
print('Using model for prediction on jpeg images ...')

make_sample_plot(model3, sample_filenames, test_samples_fig, CLASSES)

## confusion matrix
print('.....................................')
print('Computing confusion matrix and printing to '+cm_filename)

val_ds = get_validation_dataset().take(50)

labs, preds = get_label_pairs(val_ds, model3)


p_confmat(labs, preds, cm_filename, CLASSES)

#73%
