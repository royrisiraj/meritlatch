import {expect,it} from 'vitest';
import {loopbackProxy} from '../../config/loopback';
it('keeps the default proxy on loopback',()=>expect(loopbackProxy()).toBe('http://127.0.0.1:8000'));
it.each(['https://example.com','http://127.0.0.1@evil.example','http://user:secret@localhost','http://localhost/private','http://localhost?target=evil'])('rejects unsafe proxy %s',value=>expect(()=>loopbackProxy(value)).toThrow());
