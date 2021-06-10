import numpy as np
from operator import attrgetter
import matplotlib.pyplot as plt

class Task:
	def __init__(self, Tp, To, Td):
		self.Tp = Tp
		self.To = To
		self.Td = Td
		self.progress = 0
		self.interruptable = np.random.uniform() < 0.5

	def __lt__(self, other):
		return self.Tp < other.Tp

	def __repr__(self):
		return f'arrive_time: {self.Tp}, exec_time: {self.To}, deadline: {self.Td}, can be interrupted: {self.interruptable}\n'

def Stream(tact_count, frequency, exec_time, k):
	tasks = []
	start_time = 0
	while start_time + exec_time < tact_count:
		deadline = start_time + exec_time * k
		task = Task(start_time, exec_time, deadline)
		tasks.append(task)
		interval = np.random.poisson(frequency)
		start_time += interval
	return tasks

class Scheduler:
	def __init__(self, tact_count, processor_count = 1):
		self.tact_count = tact_count
		self.processor_count = processor_count
		self.downtime = 0
		self.waiting_times = []
		self.queue_sizes = [0] * self.tact_count
		self.task_count = 0
		self.expired_task_count = 0

	def get_avg_queue_size(self):
		return round(sum(self.queue_sizes) / self.tact_count)

	def get_avg_waiting_time(self):
		if not self.waiting_times:
			return 0
		return round(sum(self.waiting_times) / len(self.waiting_times))
		
	def get_downtime_percent(self):
		return round(self.downtime / self.tact_count * 100, 2)

	def get_expired_task_percent(self):
		return round(self.expired_task_count / self.task_count * 100)

	def printCharacteristics(self):
		print("Average queue size: ", self.get_avg_queue_size())
		print("Average waiting time: ", self.get_avg_waiting_time())
		print("Downtime percent: ", self.get_downtime_percent())
		print("Expired tasks count: ", self.expired_task_count)
		print("Expired tasks percent: ", self.get_expired_task_percent())

	def clearCharacteristics(self):
		self.downtime = 0
		self.waiting_times = []
		self.queue_sizes = [0] * self.tact_count
		self.task_count = 0
		self.expired_task_count = 0

	def schedule(self, stream, sorting_par = None):
		stream.sort()
		currentTasks = [None] * self.processor_count
		self.clearCharacteristics()
		queue = []
		for tact in range(self.tact_count):
			for task in stream:
				if task.Tp > tact:
					break
				queue.append(stream.pop(0))
			self.queue_sizes[tact] = len(queue)
			if sorting_par:
				queue.sort(key = attrgetter(sorting_par))
			queue.sort(key = attrgetter('interruptable'))
			for p in range(self.processor_count):
				if not currentTasks[p]:
					if not queue:
						self.downtime += 1 / self.processor_count
						continue
					else:
						currentTasks[p] = queue.pop(0)
						self.waiting_times.append(tact - currentTasks[p].Tp)
				while currentTasks[p].Td < tact:
					self.waiting_times.append(tact - currentTasks[p].Tp)
					print(f'Tact: {tact}, processor: {p}')
					print("Task expired: ", currentTasks[p])
					self.task_count += 1
					self.expired_task_count += 1
					if not queue:
						break
					currentTasks[p] = queue.pop(0)
				if sorting_par and currentTasks[p].interruptable:
					if queue:
						if getattr(queue[0], sorting_par) < getattr(currentTasks[p], sorting_par):
							stream.insert(0, currentTasks[p])
							currentTasks[p] = queue.pop(0)
				currentTasks[p].progress += 1
				if currentTasks[p].progress >= currentTasks[p].To:
					print(f'Tact: {tact}, processor: {p}')
					print("Task completed: ", currentTasks[p])
					self.task_count += 1
					currentTasks[p] = None

	def fifo(self, stream):
		print('-----FIFO---------')
		self.schedule(stream)


	def rm(self, stream):
		print('-----EDF---------')
		self.schedule(stream, 'To')
		

	def edf(self, stream):
		print('-----RM---------')
		self.schedule(stream, 'Td')

def plot_waiting_time(schedule_func):
	avg_waiting_times = [0] * 50
	for λ in range(1,50):
		t1 = Stream(100, λ, 10, 2)
		t2 = Stream(100, λ, 5, 3)
		t3 = Stream(100, λ, 20, 5)
		t = t1 + t2 + t3
		sch = Scheduler(100, 3)
		getattr(sch, schedule_func)(t)
		avg_waiting_times[λ] = round(sum(sch.waiting_times) / len(sch.waiting_times))
	plt.plot(avg_waiting_times, label = schedule_func)
	plt.xlim(1, 50)
	plt.xlabel("λ")
	plt.ylabel("Average waiting time")
	plt.title("Залежність середнього часу очікування від інтенсивності вхідного потоку заявок")

def plot_downtime_percent(schedule_func):
	downtime_percents = [0] * 50
	for λ in range(1,50):
		t1 = Stream(100, λ, 10, 2)
		t2 = Stream(100, λ, 5, 3)
		t3 = Stream(100, λ, 20, 5)
		t = t1 + t2 + t3
		sch = Scheduler(100, 3)
		getattr(sch, schedule_func)(t)
		downtime_percents[λ] = round(sch.downtime / sch.tact_count * 100, 2)
	plt.plot(downtime_percents, label = schedule_func)
	plt.xlim(1, 50)
	plt.xlabel("λ")
	plt.ylabel("Downtime percent")
	plt.title("Залежність проценту простою ресурсу від інтенсивності вхідного потоку заявок")

def plot_task_count(schedule_func):
	λ = 10
	t1 = Stream(100, λ, 10, 2)
	t2 = Stream(100, λ, 5, 3)
	t3 = Stream(100, λ, 20, 5)
	t = t1 + t2 + t3
	sch = Scheduler(100, 2)
	getattr(sch, schedule_func)(t)
	waiting_times = dict((x,sch.waiting_times.count(x)) for x in set(sch.waiting_times))
	plt.bar(range(len(waiting_times)), waiting_times.values(), label = schedule_func)
	plt.xlabel("λ")
	plt.ylabel("Average waiting time")
	plt.title("Залежність кількості заявок від часу очікування")
	sch.printCharacteristics()


def main():
	plot_task_count('fifo')
	plot_task_count('edf')
	plot_task_count('rm')
	plt.legend()
	plt.show()

	plot_waiting_time('fifo')
	plot_waiting_time('edf')
	plot_waiting_time('rm')
	plt.legend()
	plt.show()

	plot_downtime_percent('fifo')	
	plot_downtime_percent('edf')
	plot_downtime_percent('rm')
	plt.legend()
	plt.show()
main()
