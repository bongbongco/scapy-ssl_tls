#! -*- coding: utf-8 -*-

import binascii
import re
import unittest
import scapy_ssl_tls.ssl_tls as tls
import scapy_ssl_tls.ssl_tls_crypto as tlsc

from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from scapy.all import conf
from scapy.layers import x509
from scapy.layers.inet import IP, TCP

class TestTLSRecord(unittest.TestCase):

    def setUp(self):
        self.server_hello = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSServerHello()
        self.cert_list = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSCertificateList()
        self.server_hello_done = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSServerHelloDone()
        self.stacked_pkt = tls.TLS.from_records([self.server_hello, self.cert_list, self.server_hello_done])
        unittest.TestCase.setUp(self)

    def test_pkt_built_from_stacked_tls_records_is_identical(self):
        self.assertEqual(len(str(self.server_hello)), len(str(self.stacked_pkt.records[0])))
        self.assertEqual(len(str(self.cert_list)), len(str(self.stacked_pkt.records[1])))
        self.assertEqual(len(str(self.server_hello_done)), len(str(self.stacked_pkt.records[2])))
        self.assertEqual(len(str(self.server_hello)) - len(tls.TLSRecord()), self.stacked_pkt.records[0][tls.TLSRecord].length)
        self.assertEqual(len(str(self.cert_list)) - len(tls.TLSRecord()), self.stacked_pkt.records[1][tls.TLSRecord].length)
        self.assertEqual(len(str(self.server_hello_done)) - len(tls.TLSRecord()), self.stacked_pkt.records[2][tls.TLSRecord].length)

class TestTLSDissector(unittest.TestCase):

    def setUp(self):
        self.payload = binascii.unhexlify("160301004a02000046030155514d08929c06119d291bae09ec50ba48f52069c840673c76721aa5c53bc352202de1c20c707ba9b083282d2eba3d95bdfb5847eb9241f252173a04c9f990d508002f0016030104080b0004040004010003fe308203fa308202e2a003020102020900980ceed2480234b2300d06092a864886f70d0101050500305b310b3009060355040613025553311330110603550408130a43616c69666f726e696131173015060355040a130e4369747269782053797374656d73311e301c06035504031315616d73736c2e656e672e636974726974652e6e6574301e170d3135303432343233313435395a170d3235303432313233313435395a305b310b3009060355040613025553311330110603550408130a43616c69666f726e696131173015060355040a130e4369747269782053797374656d73311e301c06035504031315616d73736c2e656e672e636974726974652e6e657430820122300d06092a864886f70d01010105000382010f003082010a0282010100c0e2f8d4d4423ef7ce3e6ea789ad83c831fd679a8745bfe7d3628a544b7f04fec8bb8eb72737a6334764b68e796fbd70f19a1754776aba2f5d9685f2931b57456825ca75baca540c34de26115037d76d1a6fabbab6cd666af98fcb6b9c2fc714fd523828babae067f9ad7da51100306b4a5783a1402a4d80524dc14d0867f526e055dbd32e6f9f785072d72b8c36994bb56c2cdbf74e2149e7c625fed1c6405e205289c2b4608bd28704303764227f4540b95054c115be9185223b8a815462818090c6c933ce4c39d4049197106fe84918048adfd185fc7d64167804ccafbae8b84dc81d0288f4078c736a4ccc04c27184ffb45b14b4bd79ab472dba8877c20f0203010001a381c03081bd301d0603551d0e041604141979840d258e11dad71d942fe77e567fc0bbb48430818d0603551d2304818530818280141979840d258e11dad71d942fe77e567fc0bbb484a15fa45d305b310b3009060355040613025553311330110603550408130a43616c69666f726e696131173015060355040a130e4369747269782053797374656d73311e301c06035504031315616d73736c2e656e672e636974726974652e6e6574820900980ceed2480234b2300c0603551d13040530030101ff300d06092a864886f70d010105050003820101006fbd05d20b74d33b727fb2ccfebf3f36950278631bf87e77f503ce8e9a080925b6276f32218cadd0a43d40d89ba0e5fd9897ac536a079440385ba59e2593100df52224a8f8b786561466558d435d9ea5e4f320028ee7afa005f09b64b16f3e6b787af31b28d623edd480a50dd64fc6f0da0eab0c38c5d8965504c9c3d5c2c85514b7b1f8df9ee2d9116ac05781dbef26a66e98679f84b0378a1f8857f69e72cf72c11e836e0144153bd412dcfb506ed9e4a6181208b92be3ba9ec13f3c5b19eb700884e04a051603f2f2302d542e094afcce6694c5e46452a486b9ba339578e0f530f98824872eef62a23d685e9710c47362a034b699b7f9e1521b135e1e950d16030100040e000000")
        unittest.TestCase.setUp(self)

    def test_stacked_tls_records_are_correctly_dissected_from_bytes(self):
        # This is tls.TLSRecord()/tls.TLSHandshake()/tls.TLSServerHello()/tls.TLSRecord()/tls.TLSHandshake()/tls.TLSCertificateList()/tls.TLSRecord()/tls.TLSHandshake()/tls.TLSServerHelloDone()
        # Grabbed from the wire, with hardcoded parameters
        pkt = tls.TLS(self.payload).records
        self.assertEqual(pkt[0][tls.TLSRecord].length, 0x4a)
        self.assertEqual(pkt[0][tls.TLSHandshake].length, 0x46)
        self.assertEqual(pkt[0].gmt_unix_time, 1431391496)
        self.assertEqual(pkt[0].session_id, binascii.unhexlify("2de1c20c707ba9b083282d2eba3d95bdfb5847eb9241f252173a04c9f990d508"))
        self.assertEqual(pkt[0].cipher_suite, tls.TLSCipherSuite.RSA_WITH_AES_128_CBC_SHA)
        self.assertEqual(pkt[0].compression_method, tls.TLSCompressionMethod.NULL)
        self.assertEqual(pkt[1].length, 0x408)
        self.assertEqual(pkt[1][tls.TLSHandshake].length, 0x404)
        self.assertEqual(pkt[1][tls.TLSCertificateList].length, 0x401)
        self.assertEqual(pkt[2][tls.TLSRecord].length, 0x4)
        self.assertEqual(pkt[2][tls.TLSHandshake].type, 0x0e)

    def test_dissected_stacked_tls_records_are_identical_to_input_packet(self):
        pkt = tls.TLS(self.payload)
        self.assertEqual(len(pkt), len(self.payload))
        self.assertEqual(str(pkt), self.payload)

    def test_extensions_are_removed_when_non_specified(self):
        pkt = tls.TLS(self.payload)
        self.assertListEqual(pkt[tls.TLSServerHello].extensions, [])
        self.assertIsNone(pkt[tls.TLSServerHello].extensions_length)

class TestToRaw(unittest.TestCase):

    def setUp(self):
        self.pem_priv_key = """-----BEGIN PRIVATE KEY-----
MIIEwAIBADANBgkqhkiG9w0BAQEFAASCBKowggSmAgEAAoIBAQDDLrmt4lKRpm6P
2blptwJsa1EBuxuuAayLjwNqKGvm5c1CAUEa/NtEpUMM8WYKRDwxzakUIGI/BdP3
NOEMphcs5+OekgJLhzoSdtAIrXPy8JIidENZE6FzCJ2b6fHU5O4hoNvv1Bx5yoZr
HVaWJIZMRRocJJ0Nf9oMaU8IE6m6OdBzQHEwcnL2/a8Q3VxstHufzjILmaZD9WL+
6AESlQMKZPNQ+Xd7d4nvnVkY4ZV46tA+KvADGuotgovQwG+uiyQoGRrQUms21vHF
zIvd3G9OCiyCTCHSyfsE3g7tks33NZ8O8gF8xa9OmU9TQPwwAyUr6JQXz0CW77o7
Cr9LpHuNAgMBAAECggEBAJRbMbtfqc8XqDYjEfGur2Lld19Pb0yl7RbvD3NjYhDR
X2DqPyhaRfg5fWubGSp4jyBz6C5qJwMsVN80DFNm83qoj7T52lC6aoOaV6og3V8t
SIZzxLUyXKdpRxM5kR13HSHmeQYkPbi9HcrRM/1PqdzTMXNuyQl3wq9oZDAJchsf
fmoh080htkaxhEb1bMXa2Lj7j2OIkHOsQeIu6BdbxIKRPIT+zrcklE6ocW8fTWAS
Qi3IZ1FYLL+fs6TTxjx0VkC8QLaxWxY0pqTiwS7ndZiZKc3l3ARuvRk8buP+X3Jg
BD86FQ18OXZC9boMbDbzv2cOLtdkq5pS3lJE4F9gjYECgYEA69ukU2pNWot2OPwK
PuPwAXWNrvnvFzQgIc0qOiCmgKJU6wqunlop4Bx5XmetHExVyJVBEhaHoDr0F3Rs
gt8IclKDsWGXoVcgfu3llMimiZ05hOf/XtcGTCZwZenMQ30cFh4ZRuUu7WCZ9tqO
28P8jCXB3IcaRpRnNvVvmCr5NXECgYEA09nUzRW993SlohceRW2C9fT9HZ4BaPWO
5wVlnoo5mlUfAyzl+AGT/WlKmrn/1gAHIznQJ8ZIABQvPaBXhvkANXZP5Ie0lObw
jA7qFuKt7yV4GGlDnU1MOLh+acABMQBGSx8BJDaomH7glTiPEPTZjoP6wfAsd1uv
Knjt7jH2ad0CgYEAx9ghknRd+rx0fbBBVix4riPW20324ihOmZVnlD0aF6B0Z3tz
ncUz+irmQ7GBIpsjjIO60QK6BHAvZrhFQVaNp6B26ZORkSlr5WDZyImDYtMPa6fP
36I+OcPQNOo3I3Acnjj+ne2PJ59Ula92oIudr3pGmv72qpsQIacw2TSAWGECgYEA
sdNAN+HPMn68ZaGoLDjvW8uIB6tQnay5hhvWn8yA65YV0RGH+7Q/Z9BQ6i3EnPor
A5uMqUZbu4011jHYJpiuXzHvf/GVWAO92KLQReOCgqHd/Aen1MtEdrwOiG+90Ebd
ukLNL3ud61tc4oS2OlJ8p48LFm2mtY3FLA6UEYPoxhUCgYEAtsfWIGnBh7XC+HwI
2higSgN92VpJHSPOyOi0aG/u5AEQ+fsCUIi3KakxzvmiGMAEvWItkKyz2Gu8smtn
2HVsGxI5UW7aLw9s3qe8kyMSfUk6pGamVhJUQmDr77+5zEzykPBxwGwDwdeR43CR
xVgf/Neb/avXgIgi6drj8dp1fWA=
-----END PRIVATE KEY-----
        """
        rsa_priv_key = RSA.importKey(self.pem_priv_key)
        self.priv_key = PKCS1_v1_5.new(rsa_priv_key)
        self.pub_key = PKCS1_v1_5.new(rsa_priv_key.publickey())

        self.tls_ctx = tlsc.TLSSessionCtx()
        self.tls_ctx.rsa_load_keys(self.pem_priv_key)
        # SSLv2
        self.record_version = 0x0002
        # TLSv1.0
        self.hello_version = 0x0301
        # RSA_WITH_RC4_128_SHA
        self.cipher_suite = 0x5
        # NULL
        self.comp_method = 0x0
        self.client_hello = tls.TLSRecord(version=self.record_version)/tls.TLSHandshake()/tls.TLSClientHello(version=self.hello_version, compression_methods=[self.comp_method], cipher_suites=[self.cipher_suite])
        self.tls_ctx.insert(self.client_hello)
        self.server_hello = tls.TLSRecord(version=self.hello_version)/tls.TLSHandshake()/tls.TLSServerHello(version=self.hello_version, compression_method=self.comp_method, cipher_suite=self.cipher_suite)
        self.tls_ctx.insert(self.server_hello)
        # Build method to generate EPMS automatically in TLSSessionCtx
        self.client_kex = tls.TLSRecord(version=self.hello_version)/tls.TLSHandshake()/tls.TLSClientKeyExchange()/self.tls_ctx.get_encrypted_pms()
        self.tls_ctx.insert(self.client_kex)
        unittest.TestCase.setUp(self)

    def test_invalid_tls_session_context_raises_error(self):
        with self.assertRaises(ValueError):
            tls.to_raw(None, None)

    def test_unsupported_layer_raises_error(self):
        pkt = tls.TLSClientHello()
        with self.assertRaises(KeyError):
            tls.to_raw(pkt, self.tls_ctx)

    def test_record_payload_is_identical_to_raw_payload(self):
        pkt = tls.TLSPlaintext(data=b"ABCD")
        raw = tls.to_raw(pkt, self.tls_ctx)
        record = tls.TLSRecord()/raw
        # Length not set, until after scapy build() is called
        #self.assertEqual(record[tls.TLSRecord].length, len(raw))
        self.assertEqual(str(record[tls.TLSRecord].payload), raw)

    def test_all_hooks_are_called_when_defined(self):
        # Return the data twice, but do not compress
        def custom_compress(comp_method, pre_compress_data):
            return pre_compress_data * 2
        # Return cleartext, null mac, null padding
        pre_encrypt = lambda x: (x, b"", b"")
        # Return cleartext
        encrypt = lambda x, y, z: x
        data = b"ABCD"
        pkt = tls.TLSPlaintext(data=data)
        raw = tls.to_raw(pkt, self.tls_ctx, compress_hook=custom_compress, pre_encrypt_hook=pre_encrypt, encrypt_hook=encrypt)
        self.assertEqual(len(raw), len(data) * 2)
        self.assertEqual(raw, data * 2)

    def test_tls_record_header_is_updated_when_output(self):
        data = b"ABCD" * 389
        pkt = tls.TLSPlaintext(data=data)
        # Use server side keys, include TLSRecord header in output
        record = tls.to_raw(pkt, self.tls_ctx, client=False, include_record=True)
        self.assertTrue(record.haslayer(tls.TLSRecord))
        self.assertEqual(record.content_type, 0x17)
        self.assertEqual(record.version, self.tls_ctx.params.negotiated.version)

    def test_format_of_tls_finished_is_as_specified_in_rfc(self):
        def encrypt(cleartext, mac, padding):       
            self.assertEqual(cleartext, "\x14\x00\x00\x0c%s" % self.tls_ctx.get_verify_data()) 
            self.assertEqual(len(mac), SHA.digest_size)
            self.assertEqual(len(padding), 11)   
            self.assertTrue(all(map(lambda x: True if x == chr(11) else False, padding)))
            return "A"*48
        client_finished = tls.TLSRecord(content_type=0x16)/tls.to_raw(tls.TLSFinished(), self.tls_ctx, encrypt_hook=encrypt)
        pkt = tls.TLS(str(client_finished))
        # 4 bytes of TLSHandshake header, 12 bytes of verify_data, 20 bytes of HMAC SHA1, 11 bytes of padding, 1 padding length byte
        self.assertEqual(pkt[tls.TLSRecord].length, len(tls.TLSHandshake()) + 12 + SHA.digest_size + 11 + 1)

class TestTLSCertificate(unittest.TestCase):
    
    def setUp(self):
        '''
        //default openssl 1.0.1f server.pem
        subject= C = UK, O = OpenSSL Group, OU = FOR TESTING PURPOSES ONLY, CN = Test Server Cert
        issuer= C = UK, O = OpenSSL Group, OU = FOR TESTING PURPOSES ONLY, CN = OpenSSL Test Intermediate CA
        '''
        rex_pem = re.compile(r'\-+BEGIN[^\-]+\-+(.*?)\-+END[^\-]+\-+', re.DOTALL)
        self.pem_cert = """-----BEGIN CERTIFICATE-----
MIID5zCCAs+gAwIBAgIJALnu1NlVpZ6zMA0GCSqGSIb3DQEBBQUAMHAxCzAJBgNV
BAYTAlVLMRYwFAYDVQQKDA1PcGVuU1NMIEdyb3VwMSIwIAYDVQQLDBlGT1IgVEVT
VElORyBQVVJQT1NFUyBPTkxZMSUwIwYDVQQDDBxPcGVuU1NMIFRlc3QgSW50ZXJt
ZWRpYXRlIENBMB4XDTExMTIwODE0MDE0OFoXDTIxMTAxNjE0MDE0OFowZDELMAkG
A1UEBhMCVUsxFjAUBgNVBAoMDU9wZW5TU0wgR3JvdXAxIjAgBgNVBAsMGUZPUiBU
RVNUSU5HIFBVUlBPU0VTIE9OTFkxGTAXBgNVBAMMEFRlc3QgU2VydmVyIENlcnQw
ggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDzhPOSNtyyRspmeuUpxfNJ
KCLTuf7g3uQ4zu4iHOmRO5TQci+HhVlLZrHF9XqFXcIP0y4pWDbMSGuiorUmzmfi
R7bfSdI/+qIQt8KXRH6HNG1t8ou0VSvWId5TS5Dq/er5ODUr9OaaDva7EquHIcMv
vPQGuI+OEAcnleVCy9HVEIySrO4P3CNIicnGkwwiAud05yUAq/gPXBC1hTtmlPD7
TVcGVSEiJdvzqqlgv02qedGrkki6GY4S7GjZxrrf7Foc2EP+51LJzwLQx3/JfrCU
41NEWAsu/Sl0tQabXESN+zJ1pDqoZ3uHMgpQjeGiE0olr+YcsSW/tJmiU9OiAr8R
AgMBAAGjgY8wgYwwDAYDVR0TAQH/BAIwADAOBgNVHQ8BAf8EBAMCBeAwLAYJYIZI
AYb4QgENBB8WHU9wZW5TU0wgR2VuZXJhdGVkIENlcnRpZmljYXRlMB0GA1UdDgQW
BBSCvM8AABPR9zklmifnr9LvIBturDAfBgNVHSMEGDAWgBQ2w2yI55X+sL3szj49
hqshgYfa2jANBgkqhkiG9w0BAQUFAAOCAQEAqb1NV0B0/pbpK9Z4/bNjzPQLTRLK
WnSNm/Jh5v0GEUOE/Beg7GNjNrmeNmqxAlpqWz9qoeoFZax+QBpIZYjROU3TS3fp
yLsrnlr0CDQ5R7kCCDGa8dkXxemmpZZLbUCpW2Uoy8sAA4JjN9OtsZY7dvUXFgJ7
vVNTRnI01ghknbtD+2SxSQd3CWF6QhcRMAzZJ1z1cbbwGDDzfvGFPzJ+Sq+zEPds
xoVLLSetCiBc+40ZcDS5dV98h9XD7JMTQfxzA7mNGv73JoZJA6nFgj+ADSlJsY/t
JBv+z1iQRueoh9Qeee+ZbRifPouCB8FDx+AltvHTANdAq0t/K3o+pplMVA==
-----END CERTIFICATE-----"""
        self.der_cert = rex_pem.findall(self.pem_cert)[0].decode("base64")
        self.pem_priv_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA84TzkjbcskbKZnrlKcXzSSgi07n+4N7kOM7uIhzpkTuU0HIv
h4VZS2axxfV6hV3CD9MuKVg2zEhroqK1Js5n4ke230nSP/qiELfCl0R+hzRtbfKL
tFUr1iHeU0uQ6v3q+Tg1K/Tmmg72uxKrhyHDL7z0BriPjhAHJ5XlQsvR1RCMkqzu
D9wjSInJxpMMIgLndOclAKv4D1wQtYU7ZpTw+01XBlUhIiXb86qpYL9NqnnRq5JI
uhmOEuxo2ca63+xaHNhD/udSyc8C0Md/yX6wlONTRFgLLv0pdLUGm1xEjfsydaQ6
qGd7hzIKUI3hohNKJa/mHLElv7SZolPTogK/EQIDAQABAoIBAADq9FwNtuE5IRQn
zGtO4q7Y5uCzZ8GDNYr9RKp+P2cbuWDbvVAecYq2NV9QoIiWJOAYZKklOvekIju3
r0UZLA0PRiIrTg6NrESx3JrjWDK8QNlUO7CPTZ39/K+FrmMkV9lem9yxjJjyC34D
AQB+YRTx+l14HppjdxNwHjAVQpIx/uO2F5xAMuk32+3K+pq9CZUtrofe1q4Agj9R
5s8mSy9pbRo9kW9wl5xdEotz1LivFOEiqPUJTUq5J5PeMKao3vdK726XI4Z455Nm
W2/MA0YV0ug2FYinHcZdvKM6dimH8GLfa3X8xKRfzjGjTiMSwsdjgMa4awY3tEHH
674jhAECgYEA/zqMrc0zsbNk83sjgaYIug5kzEpN4ic020rSZsmQxSCerJTgNhmg
utKSCt0Re09Jt3LqG48msahX8ycqDsHNvlEGPQSbMu9IYeO3Wr3fAm75GEtFWePY
BhM73I7gkRt4s8bUiUepMG/wY45c5tRF23xi8foReHFFe9MDzh8fJFECgYEA9EFX
4qAik1pOJGNei9BMwmx0I0gfVEIgu0tzeVqT45vcxbxr7RkTEaDoAG6PlbWP6D9a
WQNLp4gsgRM90ZXOJ4up5DsAWDluvaF4/omabMA+MJJ5kGZ0gCj5rbZbKqUws7x8
bp+6iBfUPJUbcqNqFmi/08Yt7vrDnMnyMw2A/sECgYEAiiuRMxnuzVm34hQcsbhH
6ymVqf7j0PW2qK0F4H1ocT9qhzWFd+RB3kHWrCjnqODQoI6GbGr/4JepHUpre1ex
4UEN5oSS3G0ru0rC3U4C59dZ5KwDHFm7ffZ1pr52ljfQDUsrjjIMRtuiwNK2OoRa
WSsqiaL+SDzSB+nBmpnAizECgYBdt/y6rerWUx4MhDwwtTnel7JwHyo2MDFS6/5g
n8qC2Lj6/fMDRE22w+CA2esp7EJNQJGv+b27iFpbJEDh+/Lf5YzIT4MwVskQ5bYB
JFcmRxUVmf4e09D7o705U/DjCgMH09iCsbLmqQ38ONIRSHZaJtMDtNTHD1yi+jF+
OT43gQKBgQC/2OHZoko6iRlNOAQ/tMVFNq7fL81GivoQ9F1U0Qr+DH3ZfaH8eIkX
xT0ToMPJUzWAn8pZv0snA0um6SIgvkCuxO84OkANCVbttzXImIsL7pFzfcwV/ERK
UM6j0ZuSMFOCr/lGPAoOQU0fskidGEHi1/kW+suSr28TqsyYZpwBDQ==
-----END RSA PRIVATE KEY-----
        """
        self.der_priv_key = rex_pem.findall(self.pem_priv_key)[0].decode("base64")
        unittest.TestCase.setUp(self)
        
    def test_tls_certificate_x509(self):
        pkt = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSCertificateList(certificates=[tls.TLSCertificate(data=x509.X509Cert(self.der_cert))])
        
        self.assertEqual(str(pkt[tls.TLSCertificateList].certificates[0].data), self.der_cert)
        self.assertEqual(str(pkt[tls.TLSCertificate].data), self.der_cert)
        try:
            pkt[tls.TLSCertificate].data.pubkey
        except AttributeError, ae:
            self.fail(ae)
        # serialize and dissect the same packet
        pkt_d = tls.SSL(str(pkt))
        self.assertEqual(str(pkt_d[tls.TLSCertificateList].certificates[0].data), self.der_cert)
        self.assertEqual(str(pkt_d[tls.TLSCertificate].data), self.der_cert)
        try:
            pkt_d[tls.TLSCertificate].data.pubkey
        except AttributeError, ae:
            self.fail(ae)
        # compare pubkeys
        self.assertEqual(pkt[tls.TLSCertificate].data.pubkey, pkt_d[tls.TLSCertificate].data.pubkey)
        
    def test_tls_certificate_x509_pubkey(self):
        pkt = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSCertificateList(certificates=[tls.TLSCertificate(data=x509.X509Cert(self.der_cert))])
        # dissect and extract pubkey
        pkt = tls.SSL(str(pkt)) 
        
        pubkey_extract_from_der = tlsc.x509_extract_pubkey_from_der(self.der_cert)
        pubkey_extract_from_tls_certificate = tlsc.x509_extract_pubkey_from_der(pkt[tls.TLSCertificate].data)
        
        self.assertEqual(pubkey_extract_from_der, pubkey_extract_from_tls_certificate)

class TestTopLevelFunctions(unittest.TestCase):

    def setUp(self):
        self.server_hello = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSServerHello()
        self.cert_list = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSCertificateList()
        self.server_hello_done = tls.TLSRecord()/tls.TLSHandshake()/tls.TLSServerHelloDone()
        self.stacked_pkt = tls.TLS.from_records([self.server_hello, self.cert_list, self.server_hello_done])
        unittest.TestCase.setUp(self)

    def test_all_records_are_returned_on_iteration(self):
        records = list(tls.get_all_tls_records(self.stacked_pkt))
        self.assertEqual(str(records[0]), str(self.server_hello))
        self.assertEqual(str(records[1]), str(self.cert_list))
        self.assertEqual(str(records[2]), str(self.server_hello_done))

    def test_all_handshakes_are_returned_on_iteration(self):
        records = list(tls.get_all_tls_records(self.stacked_pkt))
        self.assertEqual(str(records[0]), str(self.server_hello))
        self.assertEqual(str(records[1]), str(self.cert_list))
        self.assertEqual(str(records[2]), str(self.server_hello_done))

    def test_leading_layers_are_ignored_from_record_list(self):
        pkt = IP()/TCP()/self.server_hello
        records = list(tls.get_all_tls_records(pkt))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0], self.server_hello)

    def test_all_layers_are_returned_upon_iteration(self):
        layers = list(tls.get_individual_layers(self.stacked_pkt))
        self.assertEqual(len(layers), 9)

if __name__ == "__main__":
    unittest.main()