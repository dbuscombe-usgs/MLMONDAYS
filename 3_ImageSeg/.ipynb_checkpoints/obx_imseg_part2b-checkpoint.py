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

from imports import *

###############################################################
### DATA FUNCTIONS
###############################################################
#-----------------------------------
def get_training_dataset(flag):
    """
    This function will return a batched dataset for model training
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: training_filenames
    OUTPUTS: batched data set object
    """
    return get_batched_dataset_obx(training_filenames, flag)

def get_validation_dataset(flag):
    """
    This function will return a batched dataset for model training
    INPUTS: None
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: validation_filenames
    OUTPUTS: batched data set object
    """
    return get_batched_dataset_obx(validation_filenames, flag)

###############################################################
## VARIABLES
###############################################################

data_path= os.getcwd()+os.sep+"data/obx"

sample_data_path = os.getcwd()+os.sep+"data/obx/sample"

sample_label_data_path = os.getcwd()+os.sep+"data/obx/sample_labels"

filepath = os.getcwd()+os.sep+'results/obx_subset_4class_best_weights_model3.h5'

hist_fig = os.getcwd()+os.sep+'results/obx_sample_4class_model3.png'

test_samples_fig = os.getcwd()+os.sep+'results/obx_sample_4class_model3_est16samples.png'

patience = 20

ims_per_shard = 20

VALIDATION_SPLIT = 0.5

###############################################################
## EXECUTION
###############################################################

#-------------------------------------------------
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

train_ds = get_training_dataset('multiclass')
val_ds = get_validation_dataset('multiclass')

# use hinge loss
print('.....................................')
print('Creating and compiling model ...')

nclasses=4
model3 = res_unet((TARGET_SIZE, TARGET_SIZE, 3), BATCH_SIZE, 'multiclass', nclasses)
model3.compile(optimizer = 'adam', loss = tf.keras.losses.CategoricalHinge(), metrics = [mean_iou])


#tf.keras.metrics.MeanIoU(num_classes=nclasses)])

# use multiclass Dice loss
# model3.compile(optimizer = 'adam', loss = multiclass_dice_coef_loss(), metrics = [mean_iou, multiclass_dice_coef])


earlystop = EarlyStopping(monitor="val_loss",
                              mode="min", patience=patience)

# set checkpoint file
model_checkpoint = ModelCheckpoint(filepath, monitor='val_loss',
                                verbose=0, save_best_only=True, mode='min',
                                save_weights_only = True)


# models are sensitive to specification of learning rate. How do you decide? Answer: you don't. Use a learning rate scheduler

lr_callback = tf.keras.callbacks.LearningRateScheduler(lambda epoch: lrfn(epoch), verbose=True)

callbacks = [model_checkpoint, earlystop, lr_callback]


do_train = False # True

if do_train:
    print('.....................................')
    print('Training model ...')
    history = model3.fit(train_ds, steps_per_epoch=steps_per_epoch, epochs=MAX_EPOCHS,
                          validation_data=val_ds, validation_steps=validation_steps,
                          callbacks=callbacks)

    # Plot training history
    plot_seg_history_iou(history, hist_fig)

    plt.close('all')
    K.clear_session()

else:
    model3.load_weights(filepath)

# ##########################################################
# ### evaluate
print('.....................................')
print('Evaluating model ...')
# testing
scores = model3.evaluate(val_ds, steps=validation_steps)

print('loss={loss:0.4f}, Mean IoU={mean_iou:0.4f}'.format(loss=scores[0], mean_iou=scores[1]))

# mean iou = 0.69

##########################################################
### predict
print('.....................................')
print('Using model for prediction on jpeg images ...')
sample_filenames = sorted(tf.io.gfile.glob(sample_data_path+os.sep+'*.jpg'))

make_sample_seg_plot(model3, sample_filenames, test_samples_fig, flag='multiclass')

#look better


print('.....................................')
print('Using model for prediction on jpeg images in ensemble mode...')

#ensemble predictions

nclasses=4
model2 = res_unet((TARGET_SIZE, TARGET_SIZE, 3), BATCH_SIZE, 'multiclass', nclasses)
model2.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = [mean_iou])
model2.load_weights(filepath.replace('model3', 'model2'))


sample_filenames = sorted(tf.io.gfile.glob(sample_data_path+os.sep+'*.jpg'))

# takes two models, and refines
# the image that is returned is that with the lowest Kullback-Leibler divergence, which is a measure of
# closeness of two probability distributions.

imgs, lbls, model_nums = make_sample_ensemble_seg_plot(model2, model3, sample_filenames, test_samples_fig.replace('.png','_crf.png'), flag='multiclass')


sample_label_filenames = sorted(tf.io.gfile.glob(sample_label_data_path+os.sep+'*.jpg'))

obs = [np.array(seg_file2tensor(f), dtype=np.uint8).squeeze() for f in sample_label_filenames]

# 0=63=deep, 1=128=broken, 2=191=shallow, 3=255=dry

# for k in range(len(obs)):
#     obs[k][obs[k]==63]=0
#     obs[k][obs[k]==128]=1
#     obs[k][obs[k]==191]=2
#     obs[k][obs[k]==255]=3

for counter in range(len(obs)):
    plt.subplot(221); plt.imshow(imgs[counter]); plt.imshow(obs[counter], alpha=0.5, cmap=plt.cm.bwr, vmin=0, vmax=255); plt.axis('off'); plt.title('Manual label', fontsize=6)
    plt.savefig('gt-example'+str(counter)+'.png', dpi=600, bbox_inches='tight'); plt.close('all')


iou = []
for k in range(len(obs)):
    i = mean_iou_np(np.expand_dims(np.expand_dims(obs[k],axis=0),axis=-1), np.expand_dims(np.expand_dims(lbls[k],axis=0),axis=-1))
    iou.append(i)

print('Mean IoU={mean_iou:0.3f}'.format(mean_iou=np.mean(iou)))

# mean iou = 0.82
