
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

#----------------------------------------------
def get_inference_model(threshold, model):
    """
    get_inference_model(threshold, model)
    This function creates an inference model consisting of an input layer for an image
    the model predictions, decoded detections, then finally a mapping from image to detections
    In effect it is a model nested in another model
    INPUTS:
        * threshold [float], the detecton probability beyond which we are confident of
        * model [keras model], trained object detection model
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: start_lr, min_lr, max_lr, rampup_epochs, sustain_epochs, exp_decay
    OUTPUTS:  keras model for detections on images
    """
    # ANY size input
    image = tf.keras.Input(shape=[None, None, 3], name="image")

    predictions = model(image, training=False)

    detections = DecodePredictions(confidence_threshold=threshold)(image, predictions)

    inference_model = tf.keras.Model(inputs=image, outputs=detections)
    return inference_model


def lrfn(epoch):
    """
    lrfn(epoch)
    This function creates a custom piecewise linear-exponential learning rate function
    for a custom learning rate scheduler. It is linear to a max, then exponentially decays
    INPUTS: current epoch number
    OPTIONAL INPUTS: None
    GLOBAL INPUTS: start_lr, min_lr, max_lr, rampup_epochs, sustain_epochs, exp_decay
    OUTPUTS:  the function lr with all arguments passed
    """
    def lr(epoch, start_lr, min_lr, max_lr, rampup_epochs, sustain_epochs, exp_decay):
        if epoch < rampup_epochs:
            lr = (max_lr - start_lr)/rampup_epochs * epoch + start_lr
        elif epoch < rampup_epochs + sustain_epochs:
            lr = max_lr
        else:
            lr = (max_lr - min_lr) * exp_decay**(epoch-rampup_epochs-sustain_epochs) + min_lr
        return lr
    return lr(epoch, start_lr, min_lr, max_lr, rampup_epochs, sustain_epochs, exp_decay)



###############################################################
## VARIABLES
###############################################################

data_path= os.getcwd()+os.sep+"data/secoora"

sample_data_path = 'data/secoora/sample'

train_hist_fig = os.getcwd()+os.sep+'results/secoora_retinanet_model1.png'

model_dir = "retinanet/"
weights_dir = "data/coco"

finetune_weights_dir = "retinanet/finetune"
sample_csv = 'data/secoora/sample.csv'

##==============================

## look at a few

val_filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*val*.tfrecord'))
train_filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*train*.tfrecord'))

train_dataset = get_test_secoora_dataset(train_filenames)

counter = 0
for sample in train_dataset.take(4):
    image = tf.image.decode_jpeg(sample['image'], channels=3)
    image = tf.cast(image, tf.float32)

    bbox = tf.numpy_function(np.array,[[sample["objects/xmin"], sample["objects/ymin"], sample["objects/xmax"], sample["objects/ymax"]]], tf.float32)
    # bbox = tf.numpy_function(np.array,[[sample["objects/xmin"].values, sample["objects/ymin"].values, sample["objects/xmax"].values, sample["objects/ymax"].values ]], tf.float32)
    bbox = tf.transpose(bbox)

    class_id = tf.cast(sample["objects/label"], dtype=tf.int32)

    scores = np.ones(bbox.shape[0])

    classes = ['person' for k in scores]

    boxes = bbox

    visualize_detections(image, boxes, classes,scores, counter, 'examples/secoora_train_examples', figsize=(16, 16), linewidth=1, color=[0, 1, 0])
    counter +=1


###############################################################
## EXECUTION
###############################################################


lr_callback = tf.keras.callbacks.LearningRateScheduler(lambda epoch: lrfn(epoch), verbose=True)

"""
## Initializing model
"""

resnet50_backbone = get_backbone()
loss_fn = RetinaNetLoss(num_classes)
model = RetinaNet(num_classes, resnet50_backbone)


"""
## Setting up callbacks, and compiling model
"""

earlystop = EarlyStopping(monitor="val_loss",
                              mode="min", patience=patience)


model_checkpoint = tf.keras.callbacks.ModelCheckpoint(
        filepath=os.path.join(model_dir, "weights" + "_epoch_{epoch}"),
        monitor="val_loss",
        save_best_only=True,
        save_weights_only=True,
        verbose=1,
    )


optimizer = tf.optimizers.SGD(momentum=0.9)
# optimizer = tf.optimizers.SGD(learning_rate=learning_rate_fn, momentum=0.9)
model.compile(loss=loss_fn, optimizer=optimizer)

latest_checkpoint = tf.train.latest_checkpoint(weights_dir)
model.load_weights(latest_checkpoint)

callbacks = [model_checkpoint, earlystop, lr_callback]


"""
## Load the Secoora dataset

"""

val_filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*val*.tfrecord'))
train_filenames = sorted(tf.io.gfile.glob(data_path+os.sep+'*train*.tfrecord'))

train_dataset, val_dataset = prepare_secoora_datasets_for_training(data_path, train_filenames, val_filenames)


"""
## Training the model
"""

# history = model.fit(
#     train_dataset, validation_data=val_dataset, epochs=MAX_EPOCHS, callbacks=callbacks)
#
# # Plot training history
# plot_history(history, train_hist_fig)
#
# plt.close('all')
# K.clear_session()


latest_checkpoint = tf.train.latest_checkpoint(finetune_weights_dir)
print(latest_checkpoint)
model.load_weights(latest_checkpoint)



## workflow for sample imagery

sample_filenames = sorted(tf.io.gfile.glob(sample_data_path+os.sep+'*.jpg'))

print(len(sample_filenames))

threshold = 0.4
inference_model = get_inference_model(threshold, model)


SCORES =[] #probability of detection
EST_NUM_PEOPLE = [] #number of people

for counter,f in enumerate(sample_filenames):
    image = file2tensor(f)

    image = tf.cast(image, dtype=tf.float32)
    input_image, ratio = prepare_image(image)
    detections = inference_model.predict(input_image)
    num_detections = detections.valid_detections[0]

    boxes = detections.nmsed_boxes[0][:num_detections] / ratio
    scores = detections.nmsed_scores[0][:num_detections]

    classes = ['person' for k in boxes]

    # visualize_detections(image, boxes, classes,scores)
    visualize_detections(image, boxes, classes,scores, counter, 'examples/secoora_weights_obrecog_part1_examples', figsize=(16, 16), linewidth=1, color=[0, 1, 0])
    SCORES.append(scores)
    EST_NUM_PEOPLE.append(len(scores))

SCORES = np.hstack(SCORES)



dat = pd.read_csv(sample_csv)
print(len(dat))

grouped = split(dat, 'filename')

SAMPLE_NUM_PEOPLE = []
for group in grouped:
    bboxs = []
    labels = []
    for index, row in group.object.iterrows():
        labels.append(class_text_to_int(row['class']))
        bboxs.append([row['xmin'], row['ymin'], row['xmax'], row['ymax']])
    SAMPLE_NUM_PEOPLE.append(len(bboxs))



plt.plot(SAMPLE_NUM_PEOPLE, NUM_PEOPLE2, 'ko')
xlim=plt.xlim()
plt.plot(xlim, xlim, 'r--')
plt.title('Observed versus estimated crowd size')
plt.xlabel('Observed number of people per frame')
plt.ylabel('Estimated number of people per frame')
plt.show()


# can we do better? train from scratch