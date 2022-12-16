import json
import psycopg2
import logging
from confluent_kafka import Consumer
from settings import DSL

logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='consumer.log',
    filemode='w'
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def save_msg(gp_con, msg, count):
	data = [value for value in json.loads(msg.value()).values()]

	cur = gp_con.cursor()
	cur.execute('INSERT INTO raw_data (sensor_id, longitude, latitude, controller_id, datetime, temperature) VALUES(%s, %s, %s, %s, %s, %s)', data)
	print('Saved!')
	logger.info(str(count) + ' - count of data at the moment')


def consume_loop(consumer, topics, gp_con, count):
	try:
		consumer.subscribe(topics)

		while True:
			msg = consumer.poll(timeout=1.0)
			if msg is None: 
				continue

			count = count + 1
			save_msg(gp_con, msg, count)

	finally:	
		consumer.close()


def run_consumer(gp_con, count):
	conf = {
		'bootstrap.servers': "127.0.0.1:9092",
        'group.id': "1",
        'auto.offset.reset': 'smallest'
    }
	consumer = Consumer(conf)

	consume_loop(consumer, ['generated-data'], gp_con, count)



def main():
	gp_con = psycopg2.connect(**DSL)
	gp_con.autocommit = True
	count = 0

	query = """CREATE TABLE raw_data (
	id SERIAL,
	sensor_id BIGINT,
	longitude FLOAT,
	latitude FLOAT,
	controller_id BIGINT,
	datetime TIMESTAMP WITH TIME ZONE,
	temperature INTEGER
);"""

	cur = gp_con.cursor()
	try:
		cur.execute(query)
	except:
		pass

	run_consumer(gp_con, count)


if __name__ == '__main__':
	main()
