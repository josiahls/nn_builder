# Run from home directory with python -m pytest tests
import shutil
import pytest
import torch
import random
import numpy as np
import torch.nn as nn

from nn_builder.pytorch.RNN import RNN
import torch.optim as optim
from torchvision import datasets, transforms


def test_user_hidden_layers_input_rejections():
    """Tests whether network rejects invalid hidden_layers inputted from user"""
    inputs_that_should_fail = [[["linearr", 33]], [["linear", 12, 33]], [["gru", 2, 33]], [["lstm", 2, 33]], [["lstmr", 33]],
                               [["gruu", 33]], [["gru", 33], ["xxx", 33]], [["linear", 33], ["gru", 12], ["gru", 33]] ]
    for input in inputs_that_should_fail:
        with pytest.raises(AssertionError):
            RNN(input_dim=1, layers=input, hidden_activations="relu",
                output_activation="relu")

def test_user_hidden_layers_input_acceptances():
    """Tests whether network rejects invalid hidden_layers inputted from user"""
    inputs_that_should_work = [[["linear", 33]], [["linear", 12]], [["gru", 2]], [["lstm", 2]], [["lstm", 1]],
                               [["gru", 330]], [["gru", 33], ["linear", 2]] ]
    for input in inputs_that_should_work:
        assert  RNN(input_dim=1, layers=input, hidden_activations="relu",
                output_activation="relu")


def test_hidden_layers_created_correctly():
    """Tests that create_hidden_layers works correctly"""
    layers = [["gru", 25], ["lstm", 23], ["linear", 5], ["linear", 10]]

    rnn = RNN(input_dim=5, layers=layers, hidden_activations="relu",
              output_activation="relu")

    assert type(rnn.hidden_layers[0]) == nn.GRU
    assert rnn.hidden_layers[0].input_size == 5
    assert rnn.hidden_layers[0].hidden_size == 25

    assert type(rnn.hidden_layers[1]) == nn.LSTM
    assert rnn.hidden_layers[1].input_size == 25
    assert rnn.hidden_layers[1].hidden_size == 23

    assert type(rnn.hidden_layers[2]) == nn.Linear
    assert rnn.hidden_layers[2].in_features == 23
    assert rnn.hidden_layers[2].out_features == 5

    assert type(rnn.output_layers[0]) == nn.Linear
    assert rnn.output_layers[0].in_features == 5
    assert rnn.output_layers[0].out_features == 10


def test_output_layers_created_correctly():
    """Tests that create_output_layers works correctly"""
    layers = [["gru", 25], ["lstm", 23], ["linear", 5], ["linear", 10]]

    rnn = RNN(input_dim=5, layers=layers, hidden_activations="relu", output_activation="relu")

    assert rnn.output_layers[0].in_features == 5
    assert rnn.output_layers[0].out_features == 10

    layers = [["gru", 25], ["lstm", 23], ["lstm", 10]]

    rnn = RNN(input_dim=5, layers=layers, hidden_activations="relu",
              output_activation="relu")

    assert rnn.output_layers[0].input_size == 23
    assert rnn.output_layers[0].hidden_size == 10

    layers = [["gru", 25], ["lstm", 23], [["lstm", 10], ["linear", 15]]]
    rnn = RNN(input_dim=5, layers=layers, hidden_activations="relu",
              output_activation="relu")

    assert rnn.output_layers[0].input_size == 23
    assert rnn.output_layers[0].hidden_size == 10

    assert rnn.output_layers[1].in_features == 23
    assert rnn.output_layers[1].out_features == 15

def test_output_dim_user_input():
    """Tests whether network rejects an invalid output_dim input from user"""
    inputs_that_should_fail = [-1, "aa", ["dd"], [2], 0, 2.5, {2}]
    for input_value in inputs_that_should_fail:
        with pytest.raises(AssertionError):
            RNN(input_dim=3, layers=[2, input_value], hidden_activations="relu",  output_activation="relu")
        with pytest.raises(AssertionError):
            RNN(input_dim=6, layers=input_value, hidden_activations="relu", output_activation="relu")

def test_activations_user_input():
    """Tests whether network rejects an invalid hidden_activations or output_activation from user"""
    inputs_that_should_fail = [-1, "aa", ["dd"], [2], 0, 2.5, {2}, "Xavier_"]
    for input_value in inputs_that_should_fail:
        with pytest.raises(AssertionError):
            RNN(input_dim=4, layers=[["linear", 2]], hidden_activations=input_value,
                output_activation="relu")
            RNN(input_dim=4, layers=[["linear", 2]], hidden_activations="relu",
                output_activation=input_value)

def test_initialiser_user_input():
    """Tests whether network rejects an invalid initialiser from user"""
    inputs_that_should_fail = [-1, "aa", ["dd"], [2], 0, 2.5, {2}, "Xavier_"]
    for input_value in inputs_that_should_fail:
        with pytest.raises(AssertionError):
            RNN(input_dim=4, layers=[["linear", 2]], hidden_activations="relu",
                output_activation="relu", initialiser=input_value)

            RNN(layers=[["linear", 2], ["linear", 2]], hidden_activations="relu",
            output_activation="relu", initialiser="xavier", input_dim=4)

def test_batch_norm_layers():
    """Tests whether batch_norm_layers method works correctly"""
    layers = [["gru", 20], ["lstm", 3], ["linear", 4], ["linear", 10]]
    rnn = RNN(layers=layers, hidden_activations="relu", input_dim=5,
              output_activation="relu", initialiser="xavier", batch_norm=True)
    assert len(rnn.batch_norm_layers) == 3
    assert rnn.batch_norm_layers[0].num_features == 20
    assert rnn.batch_norm_layers[1].num_features == 3
    assert rnn.batch_norm_layers[2].num_features == 4

def test_linear_layers_only_come_at_end():
    """Tests that it throws an error if user tries to provide list of hidden layers that include linear layers where they
    don't only come at the end"""
    layers = [["gru", 20],  ["linear", 4], ["lstm", 3], ["linear", 10]]
    with pytest.raises(AssertionError):
        rnn = RNN(layers=layers, hidden_activations="relu", input_dim=4,
                  output_activation="relu", initialiser="xavier", batch_norm=True)

    layers = [["gru", 20], ["lstm", 3],  ["linear", 4], ["linear", 10]]
    assert RNN(layers=layers, hidden_activations="relu", input_dim=4,
                      output_activation="relu", initialiser="xavier", batch_norm=True)

def test_output_activation():
    """Tests whether network outputs data that has gone through correct activation function"""
    RANDOM_ITERATIONS = 20
    input_dim = 100
    for _ in range(RANDOM_ITERATIONS):
        data = torch.randn((25, 10, 100))
        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["linear", 10], ["linear", 3]],
                           hidden_activations="relu", input_dim=input_dim,
                           output_activation="relu", initialiser="xavier", batch_norm=True)
        out = RNN_instance.forward(data)
        assert all(out.reshape(1, -1).squeeze() >= 0)

        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5]],
                           hidden_activations="relu",  input_dim=input_dim,
                           output_activation="relu", initialiser="xavier")
        out = RNN_instance.forward(data)
        assert all(out.reshape(1, -1).squeeze() >= 0)

        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["linear", 10], ["linear", 3]],
                           hidden_activations="relu", input_dim=input_dim,
                           output_activation="relu", initialiser="xavier")
        out = RNN_instance.forward(data)
        assert all(out.reshape(1, -1).squeeze() >= 0)

        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["linear", 10], ["linear", 3]],
                           hidden_activations="relu", input_dim=input_dim,
                           output_activation="sigmoid", initialiser="xavier")
        out = RNN_instance.forward(data)
        assert all(out.reshape(1, -1).squeeze() >= 0)
        assert all(out.reshape(1, -1).squeeze() <= 1)
        summed_result = torch.sum(out, dim=2)
        assert all(summed_result.reshape(1, -1).squeeze() != 1.0)


        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["linear", 10], ["linear", 3]],
                           hidden_activations="relu", input_dim=input_dim,
                           output_activation="softmax", initialiser="xavier")
        out = RNN_instance.forward(data)
        assert all(out.reshape(1, -1).squeeze() >= 0)
        assert all(out.reshape(1, -1).squeeze() <= 1)
        summed_result = torch.sum(out, dim=2)
        summed_result = summed_result.reshape(1, -1).squeeze()
        summed_result = torch.round( (summed_result * 10 ** 5) / (10 ** 5))
        assert all( summed_result == 1.0)

        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25]],
                           hidden_activations="relu", input_dim=input_dim,
                           output_activation="softmax", initialiser="xavier")
        out = RNN_instance.forward(data)
        assert all(out.reshape(1, -1).squeeze() >= 0)
        assert all(out.reshape(1, -1).squeeze() <= 1)
        summed_result = torch.sum(out, dim=2)
        summed_result = summed_result.reshape(1, -1).squeeze()
        summed_result = torch.round( (summed_result * 10 ** 5) / (10 ** 5))



        assert all( summed_result == 1.0)

        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25]],
                           hidden_activations="relu", input_dim=input_dim,
                           initialiser="xavier")
        out = RNN_instance.forward(data)
        assert not all(out.reshape(1, -1).squeeze() >= 0)

        assert not all(out.reshape(1, -1).squeeze() <= 0)
        summed_result = torch.sum(out, dim=2)
        summed_result = summed_result.reshape(1, -1).squeeze()
        summed_result = torch.round( (summed_result * 10 ** 5) / (10 ** 5))
        assert not all( summed_result == 1.0)

        RNN_instance = RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25], ["linear", 8]],
                           hidden_activations="relu", input_dim=input_dim,
                           initialiser="xavier")
        out = RNN_instance.forward(data)
        assert not all(out.reshape(1, -1).squeeze() >= 0)
        assert not all(out.reshape(1, -1).squeeze() <= 0)
        summed_result = torch.sum(out, dim=2)
        summed_result = summed_result.reshape(1, -1).squeeze()
        summed_result = torch.round( (summed_result * 10 ** 5) / (10 ** 5))
        assert not all( summed_result == 1.0)

def test_y_range():
    """Tests whether setting a y range works correctly"""
    for _ in range(100):
        val1 = random.random() - 3.0*random.random()
        val2 = random.random() + 2.0*random.random()
        lower_bound = min(val1, val2)
        upper_bound = max(val1, val2)
        rnn = RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25]],
                           hidden_activations="relu", y_range=(lower_bound, upper_bound),
                           initialiser="xavier", input_dim=22)
        random_data = torch.randn((10, 11, 22))
        out = rnn.forward(random_data)
        out = out.reshape(1, -1).squeeze()
        assert torch.sum(out > lower_bound).item() == 11*25*10, "lower {} vs. {} ".format(lower_bound, out)
        assert torch.sum(out < upper_bound).item() == 11*25*10, "upper {} vs. {} ".format(upper_bound, out)

def test_deals_with_None_activation():
    """Tests whether is able to handle user inputting None as output activation"""
    assert RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25]],
                           hidden_activations="relu", output_activation=None,
                           initialiser="xavier", input_dim=5)

def test_check_input_data_into_forward_once():
    """Tests that check_input_data_into_forward_once method only runs once"""
    rnn = RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25]],
                       hidden_activations="relu", input_dim=5,
                       output_activation="relu", initialiser="xavier")

    data_not_to_throw_error = torch.randn((1, 4, 5))
    data_to_throw_error = torch.randn((1, 2, 20))

    with pytest.raises(AssertionError):
        rnn.forward(data_to_throw_error)
    with pytest.raises(RuntimeError):
        rnn.forward(data_not_to_throw_error)
        rnn.forward(data_to_throw_error)

def test_y_range_user_input():
    """Tests whether network rejects invalid y_range inputs"""
    invalid_y_range_inputs = [ (4, 1), (2, 4, 8), [2, 4], (np.array(2.0), 6.9)]
    for y_range_value in invalid_y_range_inputs:
        with pytest.raises(AssertionError):
            print(y_range_value)
            rnn = RNN(layers=[["lstm", 20], ["gru", 5], ["lstm", 25]],
                           hidden_activations="relu", y_range=y_range_value, input_dim=5,
                           initialiser="xavier")


N = 250
X = torch.randn((N, 5, 15))
X[0:125, 0, 3] += 20.0
y = X[:, 0, 3] > 5.0
y = y.float()

def solves_simple_problem(X, y, nn_instance):
    """Checks if a given network is able to solve a simple problem"""
    optimizer = optim.Adam(nn_instance.parameters(), lr=0.15)
    for ix in range(800):
        out = nn_instance.forward(X)
        out = out[:, -1, :]
        loss = torch.sum((out.squeeze() - y) ** 2) / N
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    print("LOSS ", loss)
    return loss < 0.1

def test_model_trains():
    """Tests whether a small range of networks can solve a simple task"""
    for output_activation in ["sigmoid", "None"]:
        rnn = RNN(layers=[["gru", 20], ["lstm", 8], ["linear", 1]], input_dim=15,
                           hidden_activations="relu", output_activation=output_activation,
                           initialiser="xavier")
        assert solves_simple_problem(X, y, rnn)

    z = X[:, 0:1, 3:4] > 5.0
    z =  torch.cat([z ==1, z==0], dim=1).float()
    z = z.squeeze(-1).squeeze(-1)
    rnn = RNN(layers=[["gru", 20], ["lstm", 2]], input_dim=15,
                           hidden_activations="relu", output_activation="softmax", dropout=0.01,
                           initialiser="xavier")
    assert solves_simple_problem(X, z, rnn)

    rnn = RNN(layers=[["lstm", 20], ["linear", 1]], input_dim=15,
                       hidden_activations="relu", output_activation=None,
                       initialiser="xavier")
    assert solves_simple_problem(X, y, rnn)

    rnn = RNN(layers=[["lstm", 20], ["linear", 20], ["linear", 1]], input_dim=15,
                       hidden_activations="relu", output_activation=None,
                       initialiser="xavier", batch_norm=True)
    assert solves_simple_problem(X, y, rnn)

    rnn = RNN(layers=[["lstm", 20], ["gru", 10], ["linear", 20], ["linear", 1]], input_dim=15,
                       hidden_activations="relu", output_activation=None,
                       initialiser="xavier")
    assert solves_simple_problem(X, y, rnn)

def test_dropout():
    """Tests whether dropout layer reads in probability correctly"""
    rnn = RNN(layers=[["lstm", 20], ["gru", 10], ["linear", 20], ["linear", 1]],
                           hidden_activations="relu", output_activation="sigmoid", dropout=0.9999,
                           initialiser="xavier", input_dim=15)
    assert rnn.dropout_layer.p == 0.9999
    assert not solves_simple_problem(X, y, rnn)
    rnn = RNN(layers=[["lstm", 20], ["gru", 10], ["linear", 20], ["linear", 1]],
                           hidden_activations="relu", output_activation=None, dropout=0.0000001,
                           initialiser="xavier", input_dim=15)
    assert rnn.dropout_layer.p == 0.0000001
    assert solves_simple_problem(X, y, rnn)
