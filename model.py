import numpy as np 
import torch
import torch.nn as nn 
import torch.nn.functional as F  

def normalized_columns_initializer(weights, std=1.0):
	out = torch.randn(weights.size())
	out *= std / torch.sqrt(out.pow(2).sum(1).expand_as(out)) #var(out) = std*2
	return out

def weight_init(m):
	classname = m.__class__.__name__ 
	if classname.find('Conv') != -1: #if our class is a convolutional connection
		weight_shape = list(m.weight.data.size())
		fan_in = np.prod(weight_shape[1:4])
		fan_out = np.prod(weight_shape[2:4])*weight_shape[0]
		w_bound = np.sqrt(6. / fan_in + fan_out)
		m.weight.data.uniform_(-w_bound, +w_bound)
		m.bias.data.fill_(0)
	elif classname.find('Linear') != -1:
		weight_shape = list(m.weight.data.size())
		fan_in = weight_shape[1]
		fan_out =  weight_shape[0]
		w_bound = np.sqrt(6. / fan_in + fan_out)
		m.weight.data.uniform_(-w_bound, +w_bound)
		m.bias.data.fill_(0)		

class ActorCritic(torch.nn.Module):
	def __init__(self, num_inputs, action_space):
		super(ActorCritic, self).__init__()
		#taking care of the eyes
		self.conv1 = nn.Conv2d(num_inputs, 32, 3, stride=2, padding=1) # eyes of the network
		self.conv2 = nn.Conv2d(32, 32, 3, stride=2, padding=1) # eyes of the network
		self.conv3 = nn.Conv2d(32, 32, 3, stride=2, padding=1) # eyes of the network
		self.conv4 = nn.Conv2d(32, 32, 3, stride=2, padding=1) # eyes of the network
		#taking care of the memory, implementing LSTM
		#learn complex long term relationships between actions
		self.lstm = nn.LSTMCell(32 * 3 * 3, 256)
		num_outputs = action_space.n
		self.critic_linear = nn.Linear(256, 1)
		self.actor_linear = nn.Linear(256, num_outputs)
		self.apply(weight_init)
		self.actor_linear.weight.data = normalized_columns_initializer(self.actor_linear.weight.data, 0.01)
		self.actor_linear.bias.data.fill_(0)
		self.critic_linear.weight.data = normalized_columns_initializer(self.critic_linear.weight.data, 1)
		self.critic_linear.bias.data.fill_(0)
		self.lstm.bias_ih.data.fill_(0)
		self.lstm.bias_hh.data.fill_(0)
		self.train()

	def forward(self, inputs):
		inputs, (hx, cx) = inputs # hx = hidden node, cx = cell node
		x = F.elu(self.conv1(inputs)) #first conv layer, apply elu activation function to break linearity 
		# elu = exponential linear unit, non-linear activation function
		x = F.elu(self.conv2(x)) # second conv layer
		x = F.elu(self.conv3(x))
		x = F.elu(self.conv4(x))
		x = x.view(-1, 32*3*3) #flatten to 1 dimensional vector
		(hx, cx) = self.lstm(x, (hx, cx))
		x = hx
		return self.critic_linear(x), self.actor_linear(x), (hx, cx)

	








