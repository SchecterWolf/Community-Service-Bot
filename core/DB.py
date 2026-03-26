__author__ = "Schecter Wolf"
__copyright__ = "Copyright (C) 2026 by John Torres"
__credits__ = ["Schecter Wolf"]
__license__ = "GPLv3"
__version__ = "1.0.0"
__maintainer__ = "Schecter Wolf"
__email__ = "--"

import json
import sqlite3

from .InmateData import InmateData

from config.ClassLogger import ClassLogger, LogLevel
from config.Globals import GLOBALVARS

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Type, TypeVar

T = TypeVar("T")

class DB:
    __TABLE = "DATA"
    __TABLE_CONFIG = "CONFIG"
    __LOGGER = ClassLogger(__name__)

    def __init__(self, serverID: int):
        self.initDB = False
        self.serverID = serverID

    def getConfigAttr(self, attr: str, typ: Type[T], default: T) -> T:
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Getting config item \"{attr}\"...")
        if not self.initDB:
            self.__initDB()

        ret = default
        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        cur = conn.cursor()
        cur.execute(f"SELECT config_value FROM {DB.__TABLE_CONFIG} WHERE serverid = ? and config_name = ?;", (self.serverID, attr))
        row = cur.fetchone()

        if row:
            try:
                ret = typ(row[0])
            except Exception:
                pass

        conn.close()
        return ret

    def setConfigAttr(self, attr: str, value: Any):
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Saving config item \"{attr}\" = {value}...")
        if not self.initDB:
            self.__initDB()

        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        conn.execute(f"""
            INSERT INTO {DB.__TABLE_CONFIG} (serverid, config_name, config_value)
            VALUES (?, ?, ?)
            ON CONFLICT(serverid, config_name)
            DO UPDATE SET config_value = excluded.config_value
            """, (self.serverID, attr, str(value)))

        conn.commit()
        conn.close()

    def deleteConfigAttr(self, attr: str):
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Delete config item \"{attr}...\"")
        if not self.initDB:
            self.__initDB()

        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        conn.execute(f"""
            DELETE FROM {DB.__TABLE_CONFIG} WHERE serverid = ? AND config_name = ?
            """, (self.serverID, attr))

        conn.commit()
        conn.close()

    def getInmate(self, userID: int) -> Optional[InmateData]:
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Getting inmate data for user ({userID})...")
        if not self.initDB:
            self.__initDB()

        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        cur = conn.cursor()
        data = self.__queryData(cur, userID)

        conn.close()
        return data

    def getAllInmates(self) -> List[InmateData]:
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Getting all inmates for discord server ({self.serverID})")
        if not self.initDB:
            self.__initDB()

        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        cur = conn.cursor()

        sql = f"""
        SELECT userid FROM {DB.__TABLE} WHERE serverid = ?;
        """
        cur.execute(sql, (self.serverID,))

        inmates: List[int] = []
        for row in cur.fetchall():
            inmates.append(row[0])

        ret: List[InmateData] = []
        for inmateID in inmates:
            inmate = self.getInmate(inmateID)
            if inmate:
                ret.append(inmate)

        return ret

    def saveInmate(self, data: InmateData):
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Saving inmate data for user ({data.userid})...")
        if not self.initDB:
            self.__initDB()

        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        cur = conn.cursor()
        templ = asdict(data)
        templ["roles"] = json.dumps(list(data.roles))
        self.__commitData(cur, templ)

        conn.commit()
        conn.close()

    def deleteInmate(self, userID: int):
        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"Removing inmate data for user ({userID})...")
        if not self.initDB:
            self.__initDB()

        conn = sqlite3.connect(GLOBALVARS.FILE_DB)
        conn.execute(f"""
            DELETE FROM {DB.__TABLE} WHERE serverid = ? AND userid = ?;
            """, (self.serverID, userID))

        conn.commit()
        conn.close()

    def __queryData(self, cur: sqlite3.Cursor, userID: int) -> Optional[InmateData]:
        templ = asdict(InmateData())
        columns = ", ".join(templ.keys())
        sql = f"""
        SELECT {columns} FROM {DB.__TABLE} WHERE serverid = ? and userid = ?;
        """

        cur.execute(sql, (self.serverID, userID))
        row = cur.fetchone()

        ret = None
        if row:
            DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"fetched: {row}")
            columns = list(templ.keys())
            templ = dict(zip(columns, row))
            templ["roles"] = set(json.loads(templ.get("roles", "")))
            ret = InmateData(**templ)

        return ret

    def __commitData(self, cur: sqlite3.Cursor, data: Dict[str, Any]):
        data.pop("id")

        columns = ", ".join(data.keys())
        vals = ", ".join(["?"] * len(data.keys()))
        updateColumns = ", ".join(f"{k}=excluded.{k}" for k in data.keys() if k != "serverid" and k != "userid")

        sql = f"""
        INSERT INTO {DB.__TABLE} ({columns})
        VALUES ({vals})
        ON CONFLICT(serverid, userid)
        DO UPDATE SET {updateColumns};
        """

        DB.__LOGGER.log(LogLevel.LEVEL_DEBUG, f"{sql}\n{data}")
        cur.execute(sql, list(data.values()))

    def __initDB(self):
        conn = sqlite3.connect(GLOBALVARS.FILE_DB)

        sql = f"""
        CREATE TABLE IF NOT EXISTS {DB.__TABLE} (
            id INTEGER PRIMARY KEY,
            serverid INTEGER NOT NULL,
            userid INTEGER NOT NULL,
            roles TEXT NOT NULL,
            mode INTEGER DEFAULT 0,
            rounds INTEGER DEFAULT 0,
            timestamp INTEGER DEFAULT 0,
            UNIQUE(serverid, userid)
        )
        """
        conn.execute(sql)

        sql = f"""
        CREATE TABLE IF NOT EXISTS {DB.__TABLE_CONFIG} (
            id INTEGER PRIMARY KEY,
            serverid INTEGER NOT NULL,
            config_name TEXT NOT NULL,
            config_value TEXT NOT NULL,
            UNIQUE(serverid, config_name)
        )
        """

        conn.execute(sql)
        conn.commit()
        conn.close()

        self.initDB = True

