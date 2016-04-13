# forked from https://gist.github.com/myme5261314/005ceac0483fc5a581cc
import tensorflow as tf
import numpy as np


class RBM(object):
    def __init__(self, n_input, n_hidden, layer_names, alpha=0.1, transfer_function=tf.nn.sigmoid):
        self.n_input = n_input
        self.n_hidden = n_hidden
        self.transfer = transfer_function
        self.layer_names = layer_names

        network_weights = self._initialize_weights()
        self.weights = network_weights

        # placeholders
        self.x = tf.placeholder(tf.float32, [None, self.n_input])
        self.rbm_w = tf.placeholder(tf.float32, [self.n_input, self.n_hidden])
        self.rbm_vb = tf.placeholder(tf.float32, [self.n_input])
        self.rbm_hb = tf.placeholder(tf.float32, [self.n_hidden])

        # variables
        self.n_w = np.zeros([self.n_input, self.n_hidden], np.float32)
        self.n_vb = np.zeros([self.n_input], np.float32)
        self.n_hb = np.zeros([self.n_hidden], np.float32)
        self.o_w = np.zeros([self.n_input, self.n_hidden], np.float32)
        self.o_vb = np.zeros([self.n_input], np.float32)
        self.o_hb = np.zeros([self.n_hidden], np.float32)

        # models
        self.h0 = self.sample_prob(transfer_function(tf.matmul(self.x, self.rbm_w) + self.rbm_hb))
        self.v1 = self.sample_prob(
            transfer_function(tf.matmul(self.h0, tf.transpose(self.rbm_w)) + self.rbm_vb))
        self.h1 = tf.nn.sigmoid(tf.matmul(self.v1, self.rbm_w) + self.rbm_hb)

        # compute gradients
        self.w_positive_grad = tf.matmul(tf.transpose(self.x), self.h0)
        self.w_negative_grad = tf.matmul(tf.transpose(self.v1), self.h1)

        # compute updates and add them to weights
        self.update_w = self.rbm_w + alpha * (self.w_positive_grad - self.w_negative_grad) / tf.to_float(
            tf.shape(self.x)[0])
        self.update_vb = self.rbm_vb + alpha * tf.reduce_mean(self.x - self.v1, 0)
        self.update_hb = self.rbm_hb + alpha * tf.reduce_mean(self.h0 - self.h1, 0)

        # sampling
        self.h_sample = self.sample_prob(transfer_function(tf.matmul(self.x, self.rbm_w) + self.rbm_hb))
        self.v_sample = self.sample_prob(
            transfer_function(tf.matmul(self.h_sample, tf.transpose(self.rbm_w)) + self.rbm_vb))

        # cost
        self.err_sum = tf.reduce_mean(tf.square(self.x - self.v_sample))

        init = tf.initialize_all_variables()
        self.sess = tf.Session()
        self.sess.run(init)

    def compute_cost(self, batch):
        return self.sess.run(self.err_sum, feed_dict={self.x: batch, self.rbm_w: self.o_w,
                                                      self.rbm_vb: self.o_vb, self.rbm_hb: self.o_hb})

    def sample_prob(self, probs):
        return tf.nn.relu(tf.sign(probs - tf.random_uniform(tf.shape(probs))))

    def _initialize_weights(self):
        all_weights = dict()
        all_weights['w'] = tf.Variable(tf.random_normal([self.n_input, self.n_hidden], stddev=0.01, dtype=tf.float32),
                                       name=self.layer_names[0])
        all_weights['vb'] = tf.Variable(tf.zeros([self.n_input], dtype=tf.float32), name=self.layer_names[1])
        all_weights['hb'] = tf.Variable(tf.random_uniform([self.n_hidden], dtype=tf.float32), name=self.layer_names[2])
        return all_weights

    def transform(self, batch_x):
        return self.sess.run(self.h_sample, {self.x: batch_x, self.rbm_w: self.o_w,
                                             self.rbm_vb: self.o_vb, self.rbm_hb: self.o_hb})

    def restore_weights(self, path):
        saver = tf.train.Saver({self.layer_names[0]: self.weights['w'],
                                self.layer_names[1]: self.weights['vb'],
                                self.layer_names[2]: self.weights['hb']})

        saver.restore(self.sess, path)

        self.o_w = self.weights['w'].eval(self.sess)
        self.o_vb = self.weights['vb'].eval(self.sess)
        self.o_hb = self.weights['hb'].eval(self.sess)


    def save_weights(self, path):
        saver = tf.train.Saver({self.layer_names[0]: self.weights['w'],
                                self.layer_names[1]: self.weights['vb'],
                                self.layer_names[2]: self.weights['hb']})
        save_path = saver.save(self.sess, path)

    def return_weights(self):
        return self.weights

    def return_hidden_weight_as_np(self):
        return self.n_w

    def partial_fit(self, batch_x):
        self.n_w, self.n_vb, self.n_hb = self.sess.run([self.update_w, self.update_vb, self.update_hb],
                                                       feed_dict={self.x: batch_x, self.rbm_w: self.o_w,
                                                                  self.rbm_vb: self.o_vb, self.rbm_hb: self.o_hb})

        self.o_w = self.n_w
        self.o_vb = self.n_vb
        self.o_hb = self.n_hb

        self.sess.run(self.weights['w'].assign(self.o_w))
        self.sess.run(self.weights['vb'].assign(self.o_vb))
        self.sess.run(self.weights['hb'].assign(self.o_hb))
        return self.sess.run(self.err_sum, feed_dict={self.x: batch_x, self.rbm_w: self.n_w, self.rbm_vb: self.n_vb,
                                                      self.rbm_hb: self.n_hb})
