import tensorflow as tf
import tensorflow_text
from .claim_generator import TextualClaimGenerator


class ToTToGenerator(TextualClaimGenerator):
    """
    Generates TextualClaim objects using a t5-large model fine-tuned on the ToTTo dataset.
    The model was fine-tuned on strings encoded in 'totto' form.
    Different encodings may provide worse results.
    """
    def __init__(self, encoding, model_path, verbose=False):
        super().__init__(encoding, verbose)
        self.model = tf.saved_model.load(model_path)
        self.model_func = self.model.signatures[
            tf.saved_model.DEFAULT_SERVING_SIGNATURE_DEF_KEY
        ]
        if encoding != 'totto' and encoding != 'compact':
            raise ValueError("Invalid encoding choice. Expected 'totto' or 'compact'"
                             f"received {encoding}")
        self.encoding = encoding

    def _generate_claim(self, text):
        return self.model_func(tf.constant([text]))['outputs'].numpy()[0].decode("utf-8")
