import os
import OpenSSL
import random

from reversec.common import fs, system

from drozer.configuration import Configuration
from drozer.ssl import ca

class Provider(object):
    """
    Wraps the CA object provided by this package, to provide a DSL around key and
    certificate operations.
    """
    
    def __init__(self):
        self.authority = ca.CA()
    
    def ca_certificate_path(self):
        """
        Get the path to the CA Certificate.
        """
        
        return self.__certificate_path("drozer-ca")
    
    def ca_path(self, skip_default=False):
        """
        Get the path to the CA Key Material, as defined by the configuration file.
        """
        
        ca_path = Configuration.get("ssl", "ca_path")
        
        if ca_path == None and skip_default == False:
            ca_path = os.path.join(os.path.dirname(__file__), "embedded_ca")
        
        return ca_path

    def certificate_exists(self):
        """
        True, if the CA certificate file exists, and can be read.
        """
        
        return os.path.exists(self.ca_certificate_path())
    
    def create_keypair(self, cn):
        """
        Create a key/certificate pair, signed with the CA.
        """
        
        self.__load_key_material()
        
        key, certificate = self.authority.create_certificate(cn)
        
        fs.write(self.__certificate_path(cn), ca.CA.certificate_to_pem(certificate))
        fs.write(self.__key_path(cn), ca.CA.pkey_to_pem(key))
        
        return (key, certificate)
    
    def digest(self, certificate):
        """
        Calculate the SHA-1 digest of an X509 certificate.
        """
        
        return OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, certificate).digest('sha1')
    
    def get_keypair(self, cn, skip_default=False):
        """
        Retrieves a key pair, stored in the CA.
        """
        
        return (self.__key_path(cn, skip_default), self.__certificate_path(cn, skip_default))
        
    def key_exists(self):
        """
        True, if the CA key file exists, and can be read.
        """
        
        return self.ca_path() != None and os.path.exists(self.__ca_key_path())
    
    def key_material_exists(self):
        """
        True, if the CA Key Material exists.
        """
        
        return self.key_exists() and self.certificate_exists()
    
    def key_material_valid(self):
        """
        Tests the given Key Material, to determine if it is a valid key pair.
        """
        
        self.__load_key_material()
        
        return self.authority.verify_ca()
    
    def keypair_exists(self, cn, skip_default=False):
        """
        True, if a keypair by the specified CN exists.
        """
        
        if self.ca_path(skip_default) == None:
            return False
        
        key, certificate = self.get_keypair(cn, skip_default)
        
        return os.path.exists(key) and os.path.exists(certificate)
    
    def make_bks_key_store(self, cn, p12_path, export_password, store_password, key_password):
        """
        Prepare a BouncyCastle KeyStore from a PKCS12 bundle.
        """
        
        keytool = Configuration.executable('keytool') 
        argv = [keytool,
                "-importkeystore",
                "-deststorepass", store_password,
                "-destkeypass", key_password,
                "-destkeystore", self.__bks_path(cn),
                "-deststoretype", "BKS", 
                "-provider", "org.bouncycastle.jce.provider.BouncyCastleProvider",
                "-providerpath", os.path.abspath(os.path.join(os.path.dirname(__file__), "bcprov-ext-jdk15on-1.46.jar")),
                "-srckeystore", p12_path,
                "-srcstoretype", "PKCS12",
                "-srcstorepass", export_password,
                "-alias", "drozer"]
        
        if keytool != None:
            if os.spawnve(os.P_WAIT, argv[0], argv, os.environ) == 0:
                return self.__bks_path(cn)
        else:
            argv[0] = "keytool"
            
            print("Could not compile the BKS keystore, because keytool could not be located on your system.")
            print("Run:"                                                                                    )
            print(" ".join(argv)                                                                            )
            
            return False
    
    def make_bks_trust_store(self):
        """
        Prepare a BouncyCastle TrustStore, for the CA.
        """
        
        keytool = Configuration.executable('keytool')
        argv = [keytool,
                "-import",
                "-trustcacerts",
                "-noprompt",
                "-alias", "drozerCA",
                "-file",  self.ca_certificate_path(),
                "-keystore", self.__bks_path('drozer-ca'),
                "-storetype", "BKS",
                "-storepass", "drozer",
                "-provider", "org.bouncycastle.jce.provider.BouncyCastleProvider",
                "-providerpath", os.path.abspath(os.path.join(os.path.dirname(__file__), "bcprov-ext-jdk15on-1.46.jar"))]
        
        if keytool != None:
            if os.spawnve(os.P_WAIT, argv[0], argv, os.environ) == 0:
                return self.__bks_path('drozer-ca')
        else:
            argv[0] = "keytool"
            
            print("Could not compile the BKS trust store, because keytool could not be located on your system.")
            print("Run:"                                                                                       )
            print(" ".join(argv)                                                                               )
            
            return False
    
    def make_jks_trust_store(self):
        """
        Prepare a JKS TrustStore, for the CA.
        """
        
        keytool = Configuration.executable('keytool')
        argv = [keytool,
                "-import",
                "-trustcacerts",
                "-noprompt",
                "-alias", "drozerCA",
                "-file",  self.ca_certificate_path(),
                "-keystore", self.__jks_path('drozer-ca'),
                "-storetype", "JKS",
                "-storepass", "drozer"]
        
        if keytool != None:
            if os.spawnve(os.P_WAIT, argv[0], argv, os.environ) == 0:
                return self.__bks_path('drozer-ca')
        else:
            argv[0] = "keytool"
            
            print("Could not compile the JKS trust store, because keytool could not be located on your system.")
            print("Run:"                                                                                       )
            print(" ".join(argv)                                                                               )
            
            return False
        
    def make_pcks12(self, cn, key, cert, export_password=None):
        """
        Prepare a PKCS12 package, given a key and a certificate.
        """
        
        if export_password == None:
            export_password = ''.join(random.choice(list("abcdefghijklmnopqrstuvwxyz01234556789")) for x in range(12))
        
        pkcs12 = OpenSSL.crypto.PKCS12()
        pkcs12.set_friendlyname("drozer")
        pkcs12.set_ca_certificates([self.authority.ca_cert])
        pkcs12.set_certificate(cert)
        pkcs12.set_privatekey(key)
        
        fs.write(os.path.join(self.ca_path(), "%s.p12" % cn), pkcs12.export(export_password))
        
        return (os.path.join(self.ca_path(), "%s.p12" % cn), export_password)
        
    def provision(self, path):
        """
        Provision new CA Key Material.
        
        This will overwrite any existing CA.
        """
        
        self.authority.create_ca()
        
        Configuration.set("ssl", "ca_path", path)
        
        fs.write(self.ca_certificate_path(), ca.CA.certificate_to_pem(self.authority.ca_cert))
        fs.write(self.__ca_key_path(), ca.CA.pkey_to_pem(self.authority.ca_key))
        
        return True
    
    def trust(self, certificate, peer):
        """
        Add the certificate to the SSL Known Hosts in the Configuration file, so we will
        always trust this host in future.
        """
        
        Configuration.set("ssl-known-hosts", "%s|%d" % peer, self.digest(certificate))
    
    def trusted(self, certificate, peer):
        """
        Determine if the certificate/peer pair have been previously trusted.
        
         0 - Trusted
        -1 - Not Trusted
        -2 - Wrong Certificate
        """
        
        known_certificate = self.trusted_certificate_for(peer)
        
        if known_certificate == None:
            return -1
        elif known_certificate == self.digest(certificate):
            return 0
        else:
            return -2
    
    def trusted_certificate_for(self, peer):
        """
        Fetches the trusted certificate for a peer.
        """
        
        return Configuration.get("ssl-known-hosts", "%s|%d" % peer)
    
    def __bks_path(self, cn):
        """
        Get the path to a BouncyCastle KeyStore file.
        """
        
        return os.path.join(self.ca_path(), "%s.bks" % cn)
        
    def __ca_key_path(self):
        """
        Get the path to the CA Key.
        """
        
        return self.__key_path("drozer-ca")
    
    def __certificate_path(self, cn, skip_default=False):
        """
        Get the path to a certificate file.
        """
        
        return os.path.join(self.ca_path(skip_default), "%s.crt" % cn)
    
    def __jks_path(self, cn):
        """
        Get the path to a JKS KeyStore file.
        """
        
        return os.path.join(self.ca_path(), "%s.jks" % cn)
    
    def __key_path(self, cn, skip_default=False):
        """
        Get the path to a key file.
        """
        
        return os.path.join(self.ca_path(skip_default), "%s.key" % cn)
        
    def __load_key_material(self):
        """
        Loads Key Material into the authority, from disk.
        """
        
        if not self.authority.has_ca() and self.key_material_exists():
            self.authority.load(fs.read(self.__ca_key_path()), fs.read(self.ca_certificate_path()))
            
