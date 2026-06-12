
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_a5f60d2f6357245aa783a196bfdfc1bb = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d008ee120dd56ef864f23a31a5942001 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_cell_pop", ({ ["_open"] : false }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["position"] : "absolute", ["inset"] : "0", ["cursor"] : "default" }),onClick:on_click_d008ee120dd56ef864f23a31a5942001},)
    )
});
