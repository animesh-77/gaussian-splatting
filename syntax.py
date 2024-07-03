from tqdm import tqdm
import time, random
first_iter = 0
last_iter = 10_000
progress_bar = tqdm(range(first_iter, last_iter), desc="Training progress")

for i in range(10_000):
    time.sleep(0.0005)
    if i%10 ==0:
        progress_bar.set_postfix({"loss1": random.random(),"loss2": random.random()})
        progress_bar.update(10)
progress_bar.close()