# Technical Report: Image Classification via Convolutional Neural Networks (CNNs)

Image classification is the process of mapping a raw input—typically a pixel-based image—to a specific category label. This task is primarily performed by **Convolutional Neural Networks (CNNs)**, which mimic biological visual processing through a hierarchical, layered architecture.

![Diagram showing the hierarchical structure of a CNN from input image through convolutional and pooling layers to final classification.](images/cnn_architecture.png)

*The hierarchical architecture of a CNN, illustrating how raw pixels are transformed into high-level features through successive layers.*

---

### 1. Hierarchical Feature Extraction
The "backbone" of a CNN is designed to distill raw pixel data into increasingly sophisticated abstractions.

*   **Convolutional Layers:** These act as feature detectors. By sliding learnable filters (kernels) across the input image, the network identifies localized patterns such as edges, textures, and curves. Because these filters are shared across the image, the network can detect features regardless of their spatial location.
*   **Pooling Layers:** Following convolution, pooling (most commonly **Max Pooling**) serves to down-sample the feature maps. This provides three critical benefits:
    *   **Translation Invariance:** Allows the network to recognize an object even if it is slightly shifted or distorted.
    *   **Dimensionality Reduction:** Significantly lowers the number of parameters, reducing computational costs.
    *   **Feature Consolidation:** Helps the network focus on the most prominent features of a specific region.

---

### 2. From Features to Probabilities
Once the convolutional base has extracted high-level spatial features, these are passed to the classification "head" of the network.

![Flowchart showing flattened feature maps feeding into fully connected layers and finally the Softmax function to produce class probabilities.](images/softmax_classification.png)

*The transition from flattened feature maps to final class probabilities via fully connected layers and the Softmax function.*

*   **Fully Connected (FC) Layers:** The flattened output from the convolutional base is passed through dense layers. Here, the network performs a linear combination of inputs ($z = Wx + b$) to aggregate global information and determine how specific feature patterns correlate with specific classes. These raw output values are known as **logits**.
*   **Softmax Normalization:** Since logits are unbounded and difficult to interpret, the **Softmax function** is applied to convert them into a valid probability distribution:
    $$\sigma(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}$$
    This ensures that each output represents a value between $0$ and $1$, and that the sum of all outputs for a single image equals $1.0$.

---

### 3. Optimization and Learning
The network "learns" by iteratively adjusting its internal weights to minimize the difference between its predictions and the ground-truth labels.

| Stage | Process | Function |
| :--- | :--- | :--- |
| **Loss Function** | Categorical Cross-Entropy | Quantifies the "distance" or error between the predicted probability distribution and the actual target label. |
| **Backpropagation** | Chain Rule | Propagates the error signal backward through the network, determining the exact contribution of every weight to the total error. |
| **Optimization** | Gradient Descent | Updates the weights in the direction that reduces the loss, typically scaled by a **learning rate**. |

---

### Summary of the Classification Pipeline

1.  **Input:** Raw pixel data is fed into the network.
2.  **Forward Pass:** Data flows through convolutional, pooling, and FC layers to produce class probabilities via Softmax.
3.  **Error Measurement:** The loss function compares the network output to the known truth.
4.  **Backpropagation:** Gradients are calculated to identify how to change the weights.
5.  **Parameter Update:** Optimization algorithms modify the weights, progressively improving the accuracy of the model with each iteration.

By repeating this cycle across thousands or millions of images, the network internalizes complex visual representations, enabling it to classify previously unseen imagery with high precision.