from mrrc.pkgs.maven import handle_maven_uploading, handle_maven_del
from mrrc.storage import PRODUCT_META_KEY, CHECKSUM_META_KEY
from tests.base import BaseMRRCTest
from moto import mock_s3
import boto3
import os

TEST_BUCKET = "test_bucket"

COMMONS_CLIENT_456_INDEXES = [
    "index.html",
    "org/index.html",
    "org/apache/index.html",
    "org/apache/httpcomponents/index.html",
    "org/apache/httpcomponents/httpclient/index.html",
    "org/apache/httpcomponents/httpclient/4.5.6/index.html",
]

COMMONS_CLIENT_459_INDEXES = [
    "index.html",
    "org/index.html",
    "org/apache/index.html",
    "org/apache/httpcomponents/index.html",
    "org/apache/httpcomponents/httpclient/index.html",
    "org/apache/httpcomponents/httpclient/4.5.9/index.html",
]


COMMONS_LOGGING_INDEXES = [
    "commons-logging/index.html",
    "commons-logging/commons-logging/index.html",
    "commons-logging/commons-logging/1.2/index.html",
]

COMMONS_CLIENT_INDEX = "org/apache/httpcomponents/httpclient/index.html"
COMMONS_LOGGING_INDEX = "commons-logging/commons-logging/index.html"


@mock_s3
class MavenFileIndexTest(BaseMRRCTest):
    def setUp(self):
        super().setUp()
        # mock_s3 is used to generate expected content
        self.mock_s3 = self.__prepare_s3()
        self.mock_s3.create_bucket(Bucket=TEST_BUCKET)

    def tearDown(self):
        bucket = self.mock_s3.Bucket(TEST_BUCKET)
        try:
            bucket.objects.all().delete()
            bucket.delete()
        except ValueError:
            pass
        super().tearDown()

    def __prepare_s3(self):
        return boto3.resource('s3')

    def test_uploading_index(self):
        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.6.zip")
        product = "commons-client-4.5.6"
        handle_maven_uploading(
            test_zip, product, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )

        test_bucket = self.mock_s3.Bucket(TEST_BUCKET)
        objs = list(test_bucket.objects.all())
        self.assertEqual(30, len(objs))

        actual_files = [obj.key for obj in objs]

        for f in COMMONS_LOGGING_INDEXES:
            self.assertIn(f, actual_files)

        for f in COMMONS_CLIENT_456_INDEXES:
            self.assertIn(f, actual_files)

        for obj in objs:
            self.assertEqual(product, obj.Object().metadata[PRODUCT_META_KEY])
            self.assertIn(CHECKSUM_META_KEY, obj.Object().metadata)
            self.assertNotEqual("", obj.Object().metadata[CHECKSUM_META_KEY].strip())

        indedx_obj = test_bucket.Object(COMMONS_CLIENT_INDEX)
        index_content = str(indedx_obj.get()["Body"].read(), "utf-8")
        self.assertIn("<a href=\"4.5.6/\" title=\"4.5.6/\">4.5.6/</a>", index_content)
        self.assertIn(
            "<a href=\"maven-metadata.xml\" title=\"maven-metadata.xml\">maven-metadata.xml</a>",
            index_content
        )
        self.assertIn("<a href=\"../\" title=\"../\">../</a>", index_content)

    def test_overlap_upload_index(self):
        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.6.zip")
        product_456 = "commons-client-4.5.6"
        handle_maven_uploading(
            test_zip, product_456, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )

        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.9.zip")
        product_459 = "commons-client-4.5.9"
        handle_maven_uploading(
            test_zip, product_459, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )

        test_bucket = self.mock_s3.Bucket(TEST_BUCKET)
        objs = list(test_bucket.objects.all())
        self.assertEqual(36, len(objs))

        actual_files = [obj.key for obj in objs]
        product_mix = set([product_456, product_459])
        self.assertSetEqual(
            product_mix,
            set(
                test_bucket.Object(COMMONS_CLIENT_INDEX)
                .metadata[PRODUCT_META_KEY]
                .split(",")
            ),
        )

        for f in COMMONS_LOGGING_INDEXES:
            self.assertIn(f, actual_files)
            self.assertSetEqual(
                product_mix,
                set(test_bucket.Object(f).metadata[PRODUCT_META_KEY].split(",")),
            )

        indedx_obj = test_bucket.Object(COMMONS_CLIENT_INDEX)
        index_content = str(indedx_obj.get()["Body"].read(), "utf-8")
        self.assertIn("<a href=\"4.5.6/\" title=\"4.5.6/\">4.5.6/</a>", index_content)
        self.assertIn("<a href=\"4.5.9/\" title=\"4.5.9/\">4.5.9/</a>", index_content)
        self.assertIn(
            "<a href=\"maven-metadata.xml\" title=\"maven-metadata.xml\">maven-metadata.xml</a>",
            index_content)
        self.assertIn("<a href=\"../\" title=\"../\">../</a>", index_content)

    def test_deletion_index(self):
        self.__prepare_content()

        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.6.zip")
        product_456 = "commons-client-4.5.6"
        handle_maven_del(
            test_zip, product_456, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )

        test_bucket = self.mock_s3.Bucket(TEST_BUCKET)
        objs = list(test_bucket.objects.all())
        self.assertEqual(30, len(objs))

        actual_files = [obj.key for obj in objs]

        self.assertIn(COMMONS_CLIENT_INDEX, actual_files)

        self.assertIn(COMMONS_LOGGING_INDEX, actual_files)

        for obj in objs:
            self.assertIn(CHECKSUM_META_KEY, obj.Object().metadata)
            self.assertNotEqual("", obj.Object().metadata[CHECKSUM_META_KEY].strip())

        indedx_obj = test_bucket.Object(COMMONS_CLIENT_INDEX)
        index_content = str(indedx_obj.get()["Body"].read(), "utf-8")
        self.assertIn("<a href=\"4.5.9/\" title=\"4.5.9/\">4.5.9/</a>", index_content)
        self.assertIn("<a href=\"../\" title=\"../\">../</a>", index_content)
        self.assertIn(
            "<a href=\"maven-metadata.xml\" title=\"maven-metadata.xml\">maven-metadata.xml</a>",
            index_content)
        self.assertNotIn("<a href=\"4.5.6/\" title=\"4.5.6/\">4.5.6/</a>", index_content)

        product_459 = "commons-client-4.5.9"
        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.9.zip")
        handle_maven_del(
            test_zip, product_459, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )

        objs = list(test_bucket.objects.all())
        self.assertEqual(0, len(objs))

    def __prepare_content(self):
        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.6.zip")
        product_456 = "commons-client-4.5.6"
        handle_maven_uploading(
            test_zip, product_456, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )

        test_zip = os.path.join(os.getcwd(), "tests/input/commons-client-4.5.9.zip")
        product_459 = "commons-client-4.5.9"
        handle_maven_uploading(
            test_zip, product_459, True, bucket_name=TEST_BUCKET, dir_=self.tempdir
        )
