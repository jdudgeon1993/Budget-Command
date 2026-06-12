
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_73c7d8d22ae254f14185a3d7999fcbb3 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d008ee120dd56ef864f23a31a5942001 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.close_cell_pop", ({ ["_open"] : false }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Close",css:({ ["fontSize"] : "20px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "2px 8px", ["&:hover"] : ({ ["color"] : "#FFFFFF" }) }),onClick:on_click_d008ee120dd56ef864f23a31a5942001,role:"button",tabIndex:0},children)
    )
});
