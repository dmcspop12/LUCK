from openbachelorm.resource import Resource


def main():
    res = Resource("2.6.41", "25-09-17-05-25-13_d72007")

    ab_name_set = res.load_anon_asset()


if __name__ == "__main__":
    main()
