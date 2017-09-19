"""Proxy rotator for Scrapy. """

import base64
import random


class ProxyMiddleware(object):
    """Donwloader middleware that sets proxies for requests.

    Proxies are rotated for each request.
    """

    def __init__(self, settings):
        self.settings = settings.get('PROXY_ROTATOR')

        self.username = self.settings['username']
        self.password = self.settings['password']
        self.LUMINATI_RANDOM = self.settings['LUMINATI_RANDOM'] if 'LUMINATI_RANDOM' in self.settings

        self.proxies = read_proxies(self.settings['proxies_file'])

        self.remove_proxy_for_status_codes = \
            self.settings['remove_proxy_for_status_codes']
        self.blacklisted_proxies = []


    @classmethod
    def from_settings(cls, settings):
        """Constructs proxy middleware from specified settings.

        Args:
            settings (scrapy.settings.Settings): crawler settings.

        Returns:
            ProxyMiddleware
        """
        return ProxyMiddleware(settings)


    def process_request(self, request, spider):
        """Called for every request.

        Args:
            request (scrapy.Request)
        """
        if ('dont_proxy' not in request.meta):
            self.set_proxy(request)


    def process_response(self, request, response, spider):
        """Called for every response.

        Args:
            request (scrapy.Request)
            response (scrapy.Response)
        """

        return response


    def set_proxy(self, request):
        """Sets proxy server for request.

        Args:
            request (scrapy.Request)
        """
        u = None
        if self.LUMINATI_RANDOM:
          u = self.username + '-session-glob_rand{0}'.format(random.randrange(10 ** 11, 10 ** 12))
        else:
          u = self.username

        request.meta['proxy'] = self.random_proxy()
        request.headers['Proxy-Authorization'] = proxy_auth_header(
            u, self.password)


    def random_proxy(self):
        """
        Returns:
            str: random proxy address.
        """
        return random.choice(self.working_proxies())


    def working_proxies(self):
        """Filters only working proxies.

        Returns:
            [str]: proxy list with removed blacklisted proxies.
        """
        return filter(
            lambda proxy: proxy not in self.blacklisted_proxies,
            self.proxies
        )


    def should_remove_proxy(self, response):
        """
        Args:
            response (scrapy.Response): response object used to get status
                code.

        Returns:
            bool: True if proxy server should be blacklisted, meaning
                it will not be used for future requests.
        """
        return response.status in self.remove_proxy_for_status_codes


def proxy_auth_header(user, password):
    """
    Args:
        user (str): proxy server username.
        password (str): user password.

    Returns:
        str: proxy authentication header.
    """
    return 'Basic ' + base64.encodestring('%s:%s' % (user, password)).strip()


def read_proxies(fname):
    """Read proxy list from ips.txt.

    Returns:
        [str]: proxy IPs.
    """
    txt_file = open(fname, 'r')
    return [line.strip() for line in txt_file.readlines()]
