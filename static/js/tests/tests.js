gameon.noAnimation = true;
jasmine.DEFAULT_TIMEOUT_INTERVAL = 15000;

describe("fixtures", function () {

    it('scrambles', function () {
        var words = fixtures.scrambleWords(['a' ,'b', 'c'], [2,0,1]);
        expect(words).toEqual(['c', 'a', 'b'])

        var descrambling =  fixtures.descrambling([2,0,1]);
        expect(descrambling).toEqual([1,2,0]);

    });

});
describe("rewordgame", function () {
    beforeEach(function () {
        jasmine.clock().install();
        jasmine.clock().tick(1001);
    });
    afterEach(function () {
        jasmine.clock().uninstall();
    });

    it('lets you navigate around', function (done) {
        APP.goto('/');
        jasmine.clock().tick(1001);
        jasmine.clock().tick(1001);

        done();
    });

    it('tears down', function () {
        APP.goto('/tests');
        jasmine.clock().tick(1001);
        jasmine.clock().tick(1001);
        jasmine.clock().tick(1001);
        gameon.unblockUI();

    });
});
