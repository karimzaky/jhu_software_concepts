"""Create the applicant schema using a separately supplied administrator account."""

from load_data import CREATE_TABLE_SQL, get_connection


def main():
    """Create the table explicitly; routine application loading never creates it."""
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TABLE_SQL)
    print("Applicant schema setup completed.")


if __name__ == "__main__":
    main()
