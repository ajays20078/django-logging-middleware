""" Logging Middleware to log requests more meaningfully """
import logging
import time
from decimal import Decimal
import logging.handlers
import traceback
import json

config_file = "/etc/django_logging_middleware.json"

try:
    with open(config_file, 'r') as fh:
        config = json.load(fh)
except Exception, e:
    print "Cannot open %s" % (config_file)
    print "Exception %s" % traceback.print_exc()

LOG_FILENAME = config["CONFIG"]['log_file']
logger = logging.getLogger(LOG_FILENAME)
if config["CONFIG"]['log_level'] == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif config["CONFIG"]['log_level'] == "INFO":
    logger.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME,
    maxBytes=config["CONFIG"]['log_rotation_size'],
    backupCount=config["CONFIG"]['log_rotation_count']
)
logger.addHandler(handler)


class LoggingMiddleware(object):
    def process_request(self, request):
        self.start_time = time.time()

    def process_response(self, request, response):
        try:
            req_time = Decimal(time.time() - self.start_time)
            remote_address = (request.META.get('HTTP_X_FORWARDED_FOR') or
                              request.META.get('REMOTE_ADDR')
                              )
            content_len = len(response.content)
            user_name = "-"
            if hasattr(request, 'user'):
                user_name = getattr(request.user, 'username', '-')
            log_info = {
                'user': user_name,
                'path': request.get_full_path(),
                'status': response.status_code,
                'len': content_len,
                'time': round(req_time, 3)
            }
            if config["CONFIG"]['log_format'] == 'normal_log_format':
                log_info['client_ip'] = remote_address
                log_info['method'] = request.method
                log_info['host'] = request.get_host()
                custom_format = logging.Formatter(config["CONFIG"]
                                                  ['normal_log_format']
                                                  )
            elif config["CONFIG"]['log_format'] == 'verbose_log_format':
                log_info['request'] = request.META
                log_info['response'] = response.content
                custom_format = logging.Formatter(config["CONFIG"]
                                                  ['verbose_log_format']
                                                  )
            handler.setFormatter(custom_format)
            logger.info("", extra=log_info)
        except Exception, e:
            logger.error("Exception : %s %s" %
                         (traceback.print_exc(), e)
                         )
        return response
